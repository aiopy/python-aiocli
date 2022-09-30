from abc import ABC, abstractmethod
from argparse import Action, ArgumentParser, RawTextHelpFormatter
from dataclasses import dataclass, field
from inspect import signature
from typing import (
    Any,
    Awaitable,
    Callable,
    Container,
    Coroutine,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

__all__ = (
    # commander_app
    'State',
    'Depends',
    'CommandArgument',
    'Command',
    'command',
    'CommandHandler',
    'Application',
)

from .helpers import iscoroutinefunction, resolve_coroutine, resolve_function
from .logger import logger

CommandHandler = Callable[..., Union[Callable[[Any], Optional[int]], Coroutine[Any, Any, Optional[int]]]]


class State(Dict[Any, Any]):
    pass


# dataclass
class _Depends:
    def __init__(self, dependency: Callable[..., Any], cache: bool) -> None:
        self.dependency = dependency
        self.cache = cache


def Depends(dependency: Callable[..., Any], cache: bool = True) -> Any:
    return _Depends(dependency=dependency, cache=cache)


# https://docs.python.org/3/library/argparse.html#the-add-argument-method
class CommandArgument(NamedTuple):
    name_or_flags: Union[str, List[str]]
    action: Optional[Union[str, Action]] = None
    nargs: Optional[Union[int, str]] = None
    const: Any = None
    default: Any = None
    type: Union[Type[Any], Callable[[str], Any]] = str
    choices: Optional[Container[Any]] = None
    required: Optional[bool] = None
    help: Optional[str] = None
    metavar: Optional[str] = None
    dest: Optional[str] = None


@dataclass
class Command:
    name: str
    handler: CommandHandler
    positionals: List[
        Union[
            Tuple[str, Dict[str, Any]],
            CommandArgument,
        ]
    ] = field(default_factory=list)
    optionals: List[
        Union[
            Tuple[str, Dict[str, Any]],
            CommandArgument,
        ]
    ] = field(default_factory=list)
    deprecated: Optional[bool] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    ignore_hooks: bool = False


def command(
    name: str,
    handler: CommandHandler,
    positionals: Optional[
        List[
            Union[
                Tuple[str, Dict[str, Any]],
                CommandArgument,
            ]
        ]
    ] = None,
    optionals: Optional[
        List[
            Union[
                Tuple[str, Dict[str, Any]],
                CommandArgument,
            ]
        ]
    ] = None,
    deprecated: Optional[bool] = None,
    description: Optional[str] = None,
    usage: Optional[str] = None,
) -> Command:
    return Command(
        name=name,
        handler=handler,
        positionals=positionals or [],
        optionals=optionals or [],
        deprecated=deprecated,
        description=description,
        usage=usage,
    )


CommandMiddleware = Callable[[Command, Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]

CommandExceptionHandler = Callable[
    [BaseException, Command, Dict[str, Any]], Union[Optional[int], Coroutine[Any, Any, Optional[int]]]
]

CommandHook = Callable[['Application'], Union[None, Awaitable[None]]]

SyncArgumentState = Union[
    State,
    Dict[Any, Any],
    Callable[[], Union[State, Dict[Any, Any]]],
]

AsyncArgumentState = Callable[[], Coroutine[Any, Any, SyncArgumentState]]

ArgumentState = Union[SyncArgumentState, AsyncArgumentState]


class InternalCommandHook(ABC):
    @abstractmethod
    async def __call__(self, app: 'Application') -> None:
        pass


_yellow_color = '\033[93m'
_green_color = '\033[92m'
_close_color = '\033[00m'


@dataclass
class _ApplicationDescription:
    default_router: List[Command]
    routers: Dict[str, List[Command]]

    def _get_commands(self) -> List[Command]:
        commands = [*self.default_router]
        for commands_ in self.routers.values():
            commands += commands_
        return [command for command in commands if command.name not in ['-h', '--help', '-v', '--version']]

    def _get_spaces(self) -> int:
        number_letters_largest_command = 0
        for command_ in self._get_commands():
            if len(command_.name) > number_letters_largest_command:
                number_letters_largest_command = len(command_.name)
        return number_letters_largest_command + 2

    @staticmethod
    def _parse_router(commands: List[Command], spaces: int) -> str:
        return '\n'.join(
            [
                '  {0}{1}{2}{3}{4}'.format(
                    _green_color,
                    command.name,
                    _close_color,
                    ' ' * (spaces - len(command.name)),
                    command.description or '',
                )
                for command in commands
                if command.name not in ['-h', '--help', '-v', '--version']
            ]
        )

    def parse(self) -> str:
        spaces = self._get_spaces()
        return '{0}commands:{1}\n{2}\n{3}'.format(
            _yellow_color,
            _close_color,
            self._parse_router(self.default_router, spaces),
            '\n'.join(
                [
                    '{0}{1}{2}\n{3}'.format(_yellow_color, router, _close_color, self._parse_router(commands, spaces))
                    for router, commands in self.routers.items()
                ]
            ),
        )


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
    _app_state: Optional[State]
    _app_state_resolver: Optional[ArgumentParser]
    _default_command: str
    _use_print_for_logging: bool
    _description: _ApplicationDescription

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
        state: Optional[ArgumentState] = None,
        default_command: Optional[str] = None,
        routers: Optional[Sequence['Application']] = None,
        use_print_for_logging: bool = False,
    ) -> None:
        self._use_print_for_logging = use_print_for_logging
        self._app_state = None  # lazy
        self._app_state_resolver = state or (lambda: State())  # type: ignore
        self._parser = ArgumentParser(
            description=description,
            prog=title,
            formatter_class=RawTextHelpFormatter,
            usage='{0} [-h] [--version]{1}'.format(title, '\n\n  {0}'.format(description) if description else ''),
        )
        self._parser.add_argument('--version', action='version', version=version)
        self._parsers = {
            '-h': self._parser,
            '--help': self._parser,
            '-v': self._parser,
            '--version': self._parser,
        }
        self._debug = debug

        def self_command(name: str) -> Command:
            async def self_handler() -> int:
                _ = self._parser.parse_args([name])
                return default_exit_code

            return Command(name=name, handler=self_handler, deprecated=False, ignore_hooks=True)

        self._commands = {
            '-h': self_command('-h'),
            '--help': self_command('--help'),
            '-v': self_command('-v'),
            '--version': self_command('--version'),
        }
        self.add_commands([] if commands is None else commands)
        self._default_command = default_command or '-h'
        self._exit_code = default_exit_code
        self._middleware = [] if middleware is None else list(middleware)
        self._exception_handlers = {} if exception_handlers is None else exception_handlers
        self._on_startup = [] if on_startup is None else list(on_startup)
        self._on_shutdown = [] if on_shutdown is None else list(on_shutdown)
        self._on_cleanup = [] if on_cleanup is None else list(on_cleanup)
        self._deprecated = bool(deprecated)
        self._dependencies_cached = {}
        self._description = _ApplicationDescription(default_router=[*self._commands.values()], routers={})
        self.include_routers([] if routers is None else routers)

    async def __call__(self, args: List[str]) -> int:
        exit_code: Optional[int] = self._exit_code
        try:
            exit_code = await self._execute_command(
                name=args[0] if len(args) > 0 else self._default_command,
                args=args[1:],
            )
        except SystemExit as err:
            exit_code = err.code
        finally:
            self._exit_code = self._exit_code if exit_code is None else exit_code
        return self._exit_code

    async def _execute_command(self, name: str, args: List[str]) -> Optional[int]:
        if name not in self._parsers:
            if name:
                self._log(msg='{0}Command got "{1}".'.format('[deprecated] ' if self._deprecated else '', name))
            raise SystemExit('Missing command')
        self._log(msg='{0}Command got "{1}".'.format('[deprecated] ' if self._deprecated else '', name))
        self._log(
            msg='{0}Handler got "{1}".'.format(
                '[deprecated] ' if self._deprecated else '', self._commands[name].handler.__name__
            )
        )
        kwargs = await self._resolve_command_handler_args(name, args)
        kwargs = await self._resolve_command_handler_kwargs(self._commands[name].handler, kwargs)
        try:
            await self._execute_command_middleware(self._middleware, self._commands[name], kwargs)
            return await self._execute_command_handler(self._commands[name].handler, kwargs)
        except BaseException as err:
            return await self._execute_command_exception_handler(err, self._commands[name], kwargs)

    def include_router(self, router: 'Application') -> None:
        for name, cmd in router._commands.items():
            if name not in self._commands:
                if cmd.deprecated is None:
                    cmd.deprecated = self._deprecated
                self._commands[name] = cmd
                self._parsers[name] = router._parsers[name]
                self._update_parser_description(router._parser.prog, cmd)
        for middleware in router._middleware:
            self._middleware.append(middleware)
        self._exception_handlers.update(router._exception_handlers)
        for on_startup in router._on_startup[1:]:
            self._on_startup.append(on_startup)
        for on_shutdown in router._on_shutdown:
            self._on_shutdown.append(on_shutdown)
        for on_cleanup in router._on_cleanup:
            self._on_cleanup.append(on_cleanup)

    def include_routers(self, routers: Sequence['Application']) -> None:
        for router in routers:
            self.include_router(router=router)

    def command(
        self,
        name: str,
        *,
        positionals: Optional[
            List[
                Union[
                    Tuple[str, Dict[str, Any]],
                    CommandArgument,
                ]
            ]
        ] = None,
        optionals: Optional[
            List[
                Union[
                    Tuple[str, Dict[str, Any]],
                    CommandArgument,
                ]
            ]
        ] = None,
        deprecated: Optional[bool] = None,
        description: Optional[str] = None,
        usage: Optional[str] = None,
        ignore_hooks: bool = False,
    ) -> Callable[[CommandHandler], CommandHandler]:
        def decorator(handler: CommandHandler) -> CommandHandler:
            self._add_command(
                Command(
                    name=name,
                    handler=handler,
                    positionals=positionals or [],
                    optionals=optionals or [],
                    deprecated=deprecated,
                    description=description,
                    usage=usage,
                    ignore_hooks=ignore_hooks,
                )
            )
            return handler

        return decorator

    def should_ignore_hooks(self, args: List[str]) -> bool:
        cmd: Optional[Command] = None
        if len(args) > 0:
            cmd = self.get_command(name=args[0])
        if not cmd:
            cmd = self.get_command(name=self._default_command)
        return not cmd or cmd.ignore_hooks

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

    @classmethod
    def _resolve_state(cls, state: ArgumentState) -> State:
        if isinstance(state, State):
            return state
        if isinstance(state, Dict):
            return State(state)
        if iscoroutinefunction(state):
            return cls._resolve_state(resolve_coroutine(state))  # type: ignore
        if callable(state):
            return cls._resolve_state(state())  # type: ignore
        return State()

    def set_state(self, state: ArgumentState) -> None:
        self._app_state = self._resolve_state(state)

    @property
    def state(self) -> State:
        if self._app_state_resolver:
            self.set_state(self._app_state_resolver or (lambda: State()))  # type: ignore
            self._app_state_resolver = None

        return self._app_state  # type: ignore

    @property
    def exit_code(self) -> int:
        return self._exit_code

    def exit(self) -> None:
        self._parser.exit(status=self._exit_code)

    @property
    def on_startup(self) -> List[CommandHook]:
        return self._on_startup

    async def startup(self, all_hooks: bool = True) -> None:
        await self._execute_command_hooks(self.on_startup, all_hooks)

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
        parser = ArgumentParser(
            add_help=self._parser.add_help,
            description=cmd.description,
            formatter_class=self._parser.formatter_class,
            prefix_chars=self._parser.prefix_chars,
            prog=cmd.name,
            usage=cmd.usage,
        )
        for arg in cmd.optionals:
            if isinstance(arg, CommandArgument):
                arg = (arg.name_or_flags, arg._asdict())  # type: ignore
                del arg[1]['name_or_flags']  # type: ignore
            parser.add_argument(arg[0], **arg[1])  # type: ignore
        for arg in cmd.positionals:
            if isinstance(arg, CommandArgument):
                arg = (arg.name_or_flags, arg._asdict())  # type: ignore
                del arg[1]['name_or_flags']  # type: ignore
            if isinstance(arg[1], dict):
                if 'dest' in arg[1]:
                    del arg[1]['dest']
                if 'required' in arg[1]:
                    del arg[1]['required']
            parser.add_argument(arg[0], **arg[1])  # type: ignore
        self._parsers[cmd.name] = parser
        self._update_parser_description(self._parser.prog, cmd)

    async def _execute_command_middleware(
        self,
        command_middleware: List[CommandMiddleware],
        cmd: Command,
        kwargs: Dict[str, Any],
    ) -> None:
        for handler in command_middleware:
            self._log(
                msg='Executing middleware {0} with {1}({2})...'.format(
                    type(handler),
                    type(cmd),
                    ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()]),
                )
            )
            _ = await resolve_function(
                *([handler] if len(signature(handler).parameters) == 0 else [handler, cmd, kwargs])  # type: ignore
            )

    async def _execute_command_hooks(self, command_hooks: List[CommandHook], all_hooks: bool = True) -> None:
        command_hooks_ = (
            command_hooks if all_hooks else [hook for hook in command_hooks if isinstance(hook, InternalCommandHook)]
        )
        for hook in command_hooks_:
            if isinstance(hook, InternalCommandHook):
                hook = hook.__call__
            self._log(
                msg='Executing hook "{0}" ({1})'.format(
                    hook.__name__ if hasattr(hook, '__name__') else 'unknown', id(hook)
                )
            )
            _ = await resolve_function(
                *([hook] if len(signature(hook).parameters) == 0 else [hook, self])  # type: ignore
            )

    def _update_parser_description(self, router: Optional[str], cmd: Command) -> None:
        if router and router != 'aiocli.commander':
            self._description.routers.setdefault(router, [])
            self._description.routers[router].append(cmd)
        else:
            self._description.default_router.append(cmd)
        self._parser.description = self._description.parse()

    async def _resolve_command_handler_args(self, name: str, args: List[str]) -> Dict[str, Any]:
        if args:
            self._log(msg='Resolving args: {0}'.format(', '.join(args)))
        return vars(self._parsers[name].parse_args(args))

    async def _resolve_command_handler_kwargs(self, func: CommandHandler, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        func_params = [param for param in signature(func).parameters.values() if param.name not in kwargs]
        self._log(msg='Resolving kwargs: {0}'.format(', '.join([func_param.name for func_param in func_params])))
        kwargs_ = {**kwargs}
        for param in func_params:
            kwargs_.update(
                {
                    param.name: await self._resolve_or_retrieve_from_cache_dependency(
                        param.name, param.annotation, param.default
                    )
                }
            )
        return kwargs_

    async def _resolve_command_handler_depends_args(self, depends: _Depends, is_handler: bool = True) -> Any:
        kwargs = {}
        for param in signature(depends.dependency).parameters.values():
            self._log(
                msg='Resolving "{0}" ({1}) {2} argument for "{3}" ({4})'.format(
                    param.name,
                    id(param.name),
                    'handler' if is_handler else 'function',
                    depends.dependency.__name__,
                    id(depends.dependency),
                )
            )
            kwargs.update(
                {
                    param.name: await self._resolve_or_retrieve_from_cache_dependency(
                        param.name, param.annotation, param.default
                    )
                }
            )
            self._log(
                msg='Solved "{0}" ({1}) {2} argument for "{3}" ({4})'.format(
                    param.name,
                    id(param.name),
                    'handler' if is_handler else 'function',
                    depends.dependency.__name__,
                    id(depends.dependency),
                )
            )
        return await resolve_function(depends.dependency, **kwargs)

    async def _resolve_or_retrieve_from_cache_dependency(self, of: str, annotation: Any, value: Any) -> Any:
        if isinstance(value, _Depends):
            self._log(
                msg='Resolving "{0}" ({1}) dependency for "{2}" ({3})'.format(
                    value.dependency.__name__, id(value.dependency), of, id(of)
                )
            )
            if value.cache and value.dependency in self._dependencies_cached:
                new_value = self._dependencies_cached[value.dependency]
            else:
                new_value = await self._resolve_command_handler_depends_args(value, False)
            if value.cache:
                self._dependencies_cached.update({value.dependency: new_value})
            value = new_value
        elif isinstance(annotation, State) or issubclass(annotation, State):
            value = self.state
        return value

    async def _execute_command_handler(self, handler: CommandHandler, kwargs: Dict[str, Any]) -> int:
        self._log(
            msg='Executing command handler with: {0}'.format(
                ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()])
            ),
        )
        return cast(int, await resolve_function(handler, **kwargs))

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
        self._log(
            msg='Executing exception handler {0} with ({1})...'.format(
                type(exception_handler),
                ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()]),
            )
        )
        return cast(Optional[int], await resolve_function(exception_handler, err, cmd, kwargs))

    def _log(self, msg: str) -> None:
        if self._debug:
            if self._use_print_for_logging:
                print(msg)
            else:
                logger.debug(msg)
