from argparse import ArgumentParser, RawTextHelpFormatter
from inspect import signature
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

__all__ = (
    # commander_app
    'Command',
    'command',
    'CommandHandler',
    'Application',
    'Depends',
)

from .helpers import iscoroutinefunction
from .logger import logger

CommandHandler = Callable[..., Union[Callable[[Any], Optional[int]], Coroutine[Any, Any, Optional[int]]]]


class State:
    pass


class _Depends:
    def __init__(self, dependency: Callable[..., Any], cache: bool) -> None:
        self.dependency = dependency
        self.cache = cache


def Depends(dependency: Callable[..., Any], cache: bool = True) -> Any:
    return _Depends(dependency=dependency, cache=cache)


class Command:
    name: str
    handler: CommandHandler
    positionals: List[Tuple[str, Dict[str, Any]]]
    optionals: List[Tuple[str, Dict[str, Any]]]
    deprecated: Optional[bool]

    def __init__(
        self,
        name: str,
        handler: CommandHandler,
        positionals: List[Tuple[str, Dict[str, Any]]],
        optionals: List[Tuple[str, Dict[str, Any]]],
        deprecated: Optional[bool] = None,
    ) -> None:
        self.name = name
        self.handler = handler  # type: ignore
        self.positionals = positionals
        self.optionals = optionals
        self.deprecated = deprecated


def command(
    name: str,
    handler: CommandHandler,
    positionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    optionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    deprecated: Optional[bool] = None,
) -> Command:
    return Command(
        name=name,
        handler=handler,
        positionals=positionals or [],
        optionals=optionals or [],
        deprecated=deprecated,
    )


CommandMiddleware = Callable[[Command, Dict[str, Any]], Union[Callable[[Any], None], Coroutine[Any, Any, None]]]

CommandExceptionHandler = Callable[
    [BaseException, Command, Dict[str, Any]], Union[Optional[int], Coroutine[Any, Any, Optional[int]]]
]

CommandHook = Callable[['Application'], Union[None, Awaitable[None]]]


class Application:
    _parser: ArgumentParser
    _parsers: Dict[str, ArgumentParser]
    _debug: bool
    _commands: Dict[str, Command]
    _exit_code: int
    _middleware: List[CommandMiddleware]
    _exception_handlers: Dict[Type[BaseException], CommandExceptionHandler]
    _on_startup: List[CommandHook]
    _on_shutdown: List[CommandHook]
    _on_cleanup: List[CommandHook]
    _deprecated: bool
    _dependencies_cached: Dict[Any, Any]
    _state: State

    def __init__(
        self,
        *,
        debug: bool = False,
        commands: Optional[Sequence[Command]] = None,
        title: str = 'aiocli.commander',
        description: str = '',
        version: str = 'unknown',
        default_exit_code: int = 0,
        middleware: Optional[Sequence[CommandMiddleware]] = None,
        exception_handlers: Optional[Dict[Type[BaseException], CommandExceptionHandler]] = None,
        on_startup: Optional[Sequence[CommandHook]] = None,
        on_shutdown: Optional[Sequence[CommandHook]] = None,
        on_cleanup: Optional[Sequence[CommandHook]] = None,
        deprecated: Optional[bool] = None,
        state: Optional[State] = None,
    ) -> None:
        self._parser = ArgumentParser(
            description=description,
            prog=title,
            formatter_class=RawTextHelpFormatter,
        )
        self._parser.add_argument('--version', action='version', version=version)
        self._parsers = {}
        self._debug = debug
        self._commands = {}
        self.add_commands([] if commands is None else commands)
        self._exit_code = default_exit_code
        self._middleware = [] if middleware is None else list(middleware)
        self._exception_handlers = {} if exception_handlers is None else exception_handlers
        self._on_startup = [] if on_startup is None else list(on_startup)
        self._on_shutdown = [] if on_shutdown is None else list(on_shutdown)
        self._on_cleanup = [] if on_cleanup is None else list(on_cleanup)
        self._deprecated = bool(deprecated)
        self._dependencies_cached = {}
        self._state = State() if state is None else state

    async def __call__(self, args: List[str]) -> int:
        command_name = args[0] if len(args) > 0 else ''
        if command_name in ['-h', '--help', '--version']:
            try:
                _ = self._parser.parse_args([command_name])
            except SystemExit as err:
                self._exit_code = err.code
        elif command_name not in self._parsers:
            self._exit_code = 1
            raise ValueError('Missing command')
        else:
            if self._deprecated:
                logger.warning('Executing a deprecated command...')
            cmd = self._commands[command_name]
            handler = cmd.handler
            args = vars(self._parsers[command_name].parse_args(args[1:]))  # type: ignore
            kwargs = await self._resolve_command_handler_kwargs(handler, args)  # type: ignore
            await self._execute_command_middleware(self._middleware, cmd, kwargs)
            try:
                exit_code = await self._execute_command_handler(cmd.handler, kwargs)
            except BaseException as err:
                exit_code = await self._execute_command_exception_handler(err, cmd, kwargs)  # type: ignore
            self._exit_code = self._exit_code if exit_code is None else exit_code
        return self._exit_code

    def include_router(self, router: 'Application') -> None:
        for name, cmd in router._commands.items():
            if cmd.deprecated is None:
                cmd.deprecated = self._deprecated
            self._commands[name] = cmd
            self._parsers[name] = router._parsers[name]
            self._update_parser_description(name)
        for middleware in router._middleware:
            self._middleware.append(middleware)
        self._exception_handlers.update(router._exception_handlers)
        for on_startup in router._on_startup:
            self._on_startup.append(on_startup)
        for on_shutdown in router._on_shutdown:
            self._on_shutdown.append(on_shutdown)
        for on_cleanup in router._on_cleanup:
            self._on_cleanup.append(on_cleanup)

    def command(
        self,
        name: str,
        *,
        positionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
        optionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
        deprecated: Optional[bool] = None,
    ) -> Callable[[CommandHandler], CommandHandler]:
        def decorator(handler: CommandHandler) -> CommandHandler:
            self._add_command(
                Command(
                    name=name,
                    handler=handler,
                    positionals=positionals or [],
                    optionals=optionals or [],
                    deprecated=deprecated,
                )
            )
            return handler

        return decorator

    def add_commands(self, commands: Sequence[Command]) -> None:
        for cmd in commands:
            self._add_command(cmd)

    def get_command(self, name: str) -> Optional[Command]:
        return self._commands.get(name, None)

    def get_parser(self, command_name: str) -> Optional[ArgumentParser]:
        return self._parsers.get(command_name, None)

    def middleware(self) -> Callable[[CommandMiddleware], CommandMiddleware]:
        def decorator(middleware: CommandMiddleware) -> CommandMiddleware:
            self.add_middleware([middleware])
            return middleware

        return decorator

    def add_middleware(self, middleware: Sequence[CommandMiddleware]) -> None:
        for middleware_ in middleware:
            self._middleware.append(middleware_)

    def exception_handler(
        self,
        typ: Type[BaseException],
    ) -> Callable[[CommandExceptionHandler], CommandExceptionHandler]:
        def decorator(handler: CommandExceptionHandler) -> CommandExceptionHandler:
            self.add_exception_handlers({typ: handler})
            return handler

        return decorator

    def add_exception_handlers(self, handlers: Dict[Type[BaseException], CommandExceptionHandler]) -> None:
        self._exception_handlers.update(handlers)

    def get_exception_handler(self, typ: Type[BaseException]) -> Optional[CommandExceptionHandler]:
        return self._exception_handlers.get(typ, None)

    @property
    def parser(self) -> ArgumentParser:
        return self._parser

    @property
    def state(self) -> State:
        return self._state

    @property
    def exit_code(self) -> int:
        return self._exit_code

    def exit(self) -> None:
        self._parser.exit(status=self._exit_code)

    @property
    def on_startup(self) -> List[CommandHook]:
        return self._on_startup

    async def startup(self) -> None:
        await self._execute_command_hooks(self.on_startup)

    @property
    def on_shutdown(self) -> List[CommandHook]:
        return self._on_shutdown

    async def shutdown(self) -> None:
        await self._execute_command_hooks(self._on_shutdown)

    @property
    def on_cleanup(self) -> List[CommandHook]:
        return self._on_cleanup

    async def cleanup(self) -> None:
        await self._execute_command_hooks(self._on_cleanup)

    def _add_command(self, cmd: Command) -> None:
        if cmd.deprecated is None:
            cmd.deprecated = self._deprecated
        self._commands[cmd.name] = cmd
        parser = ArgumentParser(prog=cmd.name)
        _ = [parser.add_argument(arg[0], **arg[1]) for arg in cmd.positionals + cmd.optionals]
        self._parsers[cmd.name] = parser
        self._update_parser_description(cmd.name)

    async def _execute_command_middleware(
        self,
        command_middleware: List[CommandMiddleware],
        cmd: Command,
        kwargs: Dict[str, Any],
    ) -> None:
        for handler in command_middleware:
            if self._debug:
                logger.debug(
                    msg='Executing middleware {0} with {1}({2})...',
                    args=[
                        type(handler),
                        type(cmd),
                        ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()]),
                    ],
                )
            _ = await handler(cmd, kwargs) if iscoroutinefunction(handler) else handler(cmd, kwargs)  # type: ignore

    async def _execute_command_hooks(self, command_hooks: List[CommandHook]) -> None:
        for hook in command_hooks:
            if self._debug:
                logger.debug(
                    msg='Executing hook {0}...',
                    args=[type(hook)],
                )
            _ = await hook(self) if iscoroutinefunction(hook) else hook(self)  # type: ignore

    def _update_parser_description(self, name: str) -> None:
        self._parser.description = '{0}{1}\n'.format(self._parser.description, name)

    async def _resolve_command_handler_kwargs(self, call: CommandHandler, cmd_args: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {}
        for param in signature(call).parameters.values():
            name: str = param.name
            if name in cmd_args:
                value = cmd_args[name]
                kwargs.update({name: value})
                continue
            if name not in kwargs:
                value = await self._resolve_or_retrieve_from_cache_dependency(param.default)
                kwargs.update({name: value})
                continue
        return kwargs

    async def _resolve_command_handler_depends_args(self, depends: _Depends) -> Any:
        kwargs = {}
        for param in signature(depends.dependency).parameters.values():
            value = await self._resolve_or_retrieve_from_cache_dependency(param.default)
            kwargs.update({param.name: value})
        if iscoroutinefunction(depends.dependency):
            return await depends.dependency(**kwargs)
        return depends.dependency(**kwargs)

    async def _resolve_or_retrieve_from_cache_dependency(self, value: Any) -> Any:
        if isinstance(value, _Depends):
            if value.cache and value.dependency in self._dependencies_cached:
                new_value = self._dependencies_cached[value.dependency]
            else:
                new_value = await self._resolve_command_handler_depends_args(value)
            if value.cache:
                self._dependencies_cached.update({value.dependency: new_value})
            value = new_value
        return value

    async def _execute_command_handler(self, handler: CommandHandler, kwargs: Dict[str, Any]) -> int:
        if self._debug:
            logger.debug(
                msg='Executing command handler {0} with {1}({2})...',
                args=[type(handler), ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()])],
            )
        if iscoroutinefunction(handler):
            return await handler(**kwargs)  # type: ignore
        return handler(**kwargs)  # type: ignore

    async def _execute_command_exception_handler(
        self,
        err: BaseException,
        cmd: Command,
        kwargs: Dict[str, Any],
    ) -> Optional[int]:
        typ = type(err)
        if typ not in self._exception_handlers:
            for typ_ in list(self._exception_handlers.keys()):
                if issubclass(typ, typ_):
                    typ = typ_
                    break
            else:
                raise err
        exception_handler = self._exception_handlers[typ]
        if self._debug:
            logger.debug(
                msg='Executing exception handler {0} with {1}({2})...',
                args=[
                    type(exception_handler),
                    type(err),
                    ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()]),
                ],
            )
        if iscoroutinefunction(exception_handler):
            return await exception_handler(err, cmd, kwargs)  # type: ignore
        return exception_handler(err, cmd, kwargs)  # type: ignore
