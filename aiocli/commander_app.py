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
    'InternalCommandHook',
)

from .helpers import iscoroutinefunction, resolve_coroutine, resolve_function
from .logger import logger

CommandHandler = Callable[
    ...,
    Union[
        Callable[[Any], Any],
        Coroutine[Any, Any, Any],
    ],
]


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
    required: Optional[bool] = None  # only for optionals
    help: Optional[str] = None
    metavar: Optional[str] = None
    dest: Optional[str] = None  # only for optionals

    def dict(self, optional: bool) -> Tuple[Union[str, List[str]], Dict[str, Any]]:
        kwargs = {
            'action': self.action,
            'nargs': self.nargs,
            'const': self.const,
            'default': self.default,
            'type': self.type,
            'choices': self.choices,
            'help': self.help,
            'metavar': self.metavar,
        }
        if optional:
            kwargs['dest'] = self.dest
            kwargs['required'] = self.required
        return self.name_or_flags, kwargs


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
    ignore_middleware: bool = False

    def should_ignore_internal_hooks(self) -> bool:
        return self.ignore_hooks and self.name in ['-h', '--help', '-v', '--version']

    def should_ignore_middleware(self) -> bool:
        return self.ignore_middleware and self.name in ['-h', '--help', '-v', '--version']


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


CommandMiddleware = Callable[[Command, Dict[str, Any], 'Application'], Union[None, Coroutine[Any, Any, None]]]

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
    color: bool

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

    def _parse_router(self, commands: List[Command], spaces: int) -> str:
        return '\n'.join(
            [
                '  {0}{1}{2}{3}{4}'.format(
                    _green_color if self.color else '',
                    command.name,
                    _close_color if self.color else '',
                    ' ' * (spaces - len(command.name)),
                    command.description or '',
                )
                for command in commands
                if command.name not in ['-h', '--help', '-v', '--version']
            ]
        )

    def parse(self) -> str:
        spaces = self._get_spaces()
        return '{0}Available commands:{1}\n{2}\n{3}'.format(
            _yellow_color if self.color else '',
            _close_color if self.color else '',
            self._parse_router(self.default_router, spaces),
            '\n'.join(
                [
                    '{0} {1}{2}\n{3}'.format(
                        _yellow_color if self.color else '',
                        router,
                        _close_color if self.color else '',
                        self._parse_router(commands, spaces),
                    )
                    for router, commands in self.routers.items()
                ]
            ),
        )


class ApplicationHelpFormatter(RawTextHelpFormatter):
    color: bool

    def _format_usage(self, usage: Any, actions: Any, groups: Any, prefix: Any) -> str:
        return super()._format_usage(
            usage,
            actions,
            groups,
            '{0}Usage: {1}'.format(_yellow_color if self.color else '', _close_color if self.color else ''),
        )


ApplicationRawInput = Tuple[Tuple[Any, ...], Dict[str, Any]]


class Application:
    _parser: ArgumentParser
    _parsers: Dict[str, ArgumentParser]
    _debug: bool
    _commands: Dict[str, Command]
    _exit_code: int
    _before_middleware: List[CommandMiddleware]
    _after_middleware: List[CommandMiddleware]
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
    _color: bool
    _raw_input: ApplicationRawInput
    _override_return: bool

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
        after_middleware: Optional[Sequence[CommandMiddleware]] = None,
        exception_handlers: Optional[Dict[Type[BaseException], CommandExceptionHandler]] = None,
        on_startup: Optional[Sequence[CommandHook]] = None,
        on_shutdown: Optional[Sequence[CommandHook]] = None,
        on_cleanup: Optional[Sequence[CommandHook]] = None,
        deprecated: Optional[bool] = None,
        state: Optional[ArgumentState] = None,
        default_command: Optional[str] = None,
        routers: Optional[Sequence['Application']] = None,
        use_print_for_logging: bool = False,
        color: bool = True,
        override_return: bool = False,  # if False CommandHandler output will be taken as exit code
    ) -> None:
        self._raw_input = (
            (),
            {},
        )  # lazy
        self._override_return = override_return
        self._color = color
        self._use_print_for_logging = use_print_for_logging
        self._app_state = None  # lazy
        self._app_state_resolver = state or (lambda: State())  # type: ignore

        class InternalApplicationHelpFormatter(ApplicationHelpFormatter):
            color = self._color

        self._parser = ArgumentParser(
            description=description,
            prog=title,
            formatter_class=InternalApplicationHelpFormatter,
            usage='{0} [-h] [--version]{1}'.format(title, '\n\n  {0}'.format(description) if description else ''),
        )
        self._update_parser_help(self._parser, cast(str, self.parser.usage))
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

            return Command(name=name, handler=self_handler, deprecated=False, ignore_hooks=True, ignore_middleware=True)

        self._commands = {
            '-h': self_command('-h'),
            '--help': self_command('--help'),
            '-v': self_command('-v'),
            '--version': self_command('--version'),
        }
        self.add_commands([] if commands is None else commands)
        self._default_command = default_command or '-h'
        self._exit_code = default_exit_code
        self._before_middleware = [] if middleware is None else list(middleware)
        self._after_middleware = [] if after_middleware is None else list(after_middleware)
        self._exception_handlers = {} if exception_handlers is None else exception_handlers
        self._on_startup = [] if on_startup is None else list(on_startup)
        self._on_shutdown = [] if on_shutdown is None else list(on_shutdown)
        self._on_cleanup = [] if on_cleanup is None else list(on_cleanup)
        self._deprecated = bool(deprecated)
        self._dependencies_cached = {}
        self._description = _ApplicationDescription(default_router=[*self._commands.values()], routers={}, color=color)
        self.include_routers([] if routers is None else routers)

    async def __call__(self, args: List[str]) -> Any:
        response: Any = self._exit_code
        try:
            response = await self._execute_command(
                name=args[0] if len(args) > 0 else self._default_command,
                args=args[1:],
            )
        except SystemExit as err:
            response = err.code
        finally:
            if not self._override_return and isinstance(response, int) and 0 <= response <= 255:
                self._exit_code = response
        return response if self._override_return else self._exit_code

    def _ensure_command_exists(self, name: str) -> None:
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

    async def _execute_command(self, name: str, args: List[str]) -> Any:
        self._ensure_command_exists(name=name)
        kwargs = await self._resolve_command_handler_args(name, args)
        kwargs = await self._resolve_command_handler_kwargs(self._commands[name].handler, kwargs)
        try:
            await self._execute_command_middleware(self._before_middleware, self._commands[name], kwargs)
            response = await self._execute_command_handler(self._commands[name].handler, kwargs)
            await self._execute_command_middleware(self._after_middleware, self._commands[name], kwargs)
            return response
        except BaseException as err:
            return await self._execute_command_exception_handler(err, self._commands[name], kwargs)

    def include_router(self, router: 'Application') -> None:
        for name, cmd in router._commands.items():
            if name not in self._commands:
                if cmd.deprecated is None:
                    cmd.deprecated = self._deprecated
                self._commands[name] = cmd
                self._parsers[name] = router._parsers[name]
                self._update_main_parser_description(router._parser, cmd)
        self._before_middleware.extend(router._before_middleware)
        self._after_middleware.extend(router._after_middleware)
        self._exception_handlers.update(router._exception_handlers)
        self._on_startup.extend(router._on_startup)
        self._on_shutdown.extend(router._on_shutdown)
        self._on_cleanup.extend(router.on_cleanup)
        self._render_parser()

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

    def _get_command_from_args(self, args: List[str]) -> Optional[Command]:
        cmd: Optional[Command] = None
        if len(args) > 0:
            cmd = self.get_command(name=args[0])
        if not cmd:
            cmd = self.get_command(name=self._default_command)
        return cmd

    def should_ignore_hooks(self, args: List[str]) -> bool:
        cmd = self._get_command_from_args(args=args)
        return not cmd or cmd.ignore_hooks

    def should_ignore_internal_hooks(self, args: List[str]) -> bool:
        cmd = self._get_command_from_args(args=args)
        return not cmd or cmd.should_ignore_internal_hooks() or args[-1] in ['-h', '--help', '-v', '--version']

    def add_commands(self, commands: Sequence[Command]) -> None:
        for cmd in commands:
            self._add_command(cmd)

    def get_command(self, name: str) -> Optional[Command]:
        return self._commands.get(name, None)

    def get_parser(self, command_name: str) -> Optional[ArgumentParser]:
        return self._parsers.get(command_name, None)

    def middleware(self, after: bool = False) -> Callable[[CommandMiddleware], CommandMiddleware]:
        def decorator(middleware: CommandMiddleware) -> CommandMiddleware:
            self.add_middleware(middleware=[middleware], after=after)
            return middleware

        return decorator

    def add_middleware(self, middleware: Sequence[CommandMiddleware], after: bool = False) -> None:
        if after:
            self._after_middleware.extend(middleware)
        else:
            self._before_middleware.extend(middleware)

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

    async def startup(self, all_hooks: bool = True, ignore_internal_hooks: bool = False) -> None:
        await self._execute_command_hooks(self.on_startup, all_hooks, ignore_internal_hooks)

    @property
    def on_shutdown(self) -> List[CommandHook]:
        return self._on_shutdown

    async def shutdown(self, all_hooks: bool = True, ignore_internal_hooks: bool = False) -> None:
        await self._execute_command_hooks(self._on_shutdown, all_hooks, ignore_internal_hooks)

    @property
    def on_cleanup(self) -> List[CommandHook]:
        return self._on_cleanup

    async def cleanup(self, all_hooks: bool = True, ignore_internal_hooks: bool = False) -> None:
        await self._execute_command_hooks(self._on_cleanup, all_hooks, ignore_internal_hooks)

    def colorize(self, color: bool) -> None:
        self._color = color
        self._render_parser()

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
                arg = arg.dict(optional=True)  # type: ignore
            parser.add_argument(arg[0], **arg[1])  # type: ignore
        for arg in cmd.positionals:
            if isinstance(arg, CommandArgument):
                arg = arg.dict(optional=False)  # type: ignore
            parser.add_argument(arg[0], **arg[1])  # type: ignore
        self._update_parser_help(parser, cmd.name)
        self._parsers[cmd.name] = parser
        self._update_main_parser_description(self._parser, cmd)

    async def _execute_command_middleware(
        self,
        command_middleware: List[CommandMiddleware],
        cmd: Command,
        kwargs: Dict[str, Any],
    ) -> None:
        if cmd.should_ignore_middleware():
            self._log(msg='Command middleware ignored')
            return
        for handler in command_middleware:
            self._log(
                msg='Executing middleware {0} with {1}({2})...'.format(
                    type(handler),
                    type(cmd),
                    ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()]),
                )
            )
            parameters_count = len(signature(handler).parameters)

            function_args: List[Any] = []
            if parameters_count == 0:
                function_args = []
            elif parameters_count == 1:
                function_args = [cmd]
            elif parameters_count == 2:
                function_args = [cmd, kwargs]
            elif parameters_count == 3:
                function_args = [cmd, kwargs, self]
            else:
                raise IndexError('Invalid number of parameters to resolve CommandMiddleware')

            _ = await resolve_function(handler, *function_args)

    async def _execute_command_hooks(
        self,
        command_hooks: List[CommandHook],
        all_hooks: bool = True,
        ignore_internal_hooks: bool = False,
    ) -> None:
        command_hooks_ = (
            command_hooks
            if all_hooks
            else [hook for hook in command_hooks if isinstance(hook, InternalCommandHook) and not ignore_internal_hooks]
        )
        for hook in command_hooks_:
            if isinstance(hook, InternalCommandHook):
                hook = hook.__call__
            self._log(
                msg='Executing hook "{0}" ({1})'.format(
                    hook.__name__ if hasattr(hook, '__name__') else 'unknown', id(hook)
                )
            )

            parameters_count = len(signature(hook).parameters)

            if parameters_count == 0:
                function_args = [hook]
            elif parameters_count == 1:
                function_args = [hook, self]  # type: ignore
            else:
                raise IndexError('Invalid number of parameters to resolve CommandHook')

            _ = await resolve_function(*function_args)

    async def _resolve_command_handler_args(self, name: str, args: List[str]) -> Dict[str, Any]:
        if args:
            self._log(msg='Resolving args: {0}'.format(', '.join(args)))
        return vars(self._parsers[name].parse_args(args))

    async def _resolve_command_handler_kwargs(self, func: CommandHandler, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        func_params = [param for param in signature(func).parameters.values() if param.name not in kwargs]
        if func_params:
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

    async def _execute_command_handler(self, handler: CommandHandler, kwargs: Dict[str, Any]) -> Any:
        self._log(
            msg='Executing command handler with: {0}.'.format(
                ', '.join(['{0}={1}'.format(key, val) for key, val in kwargs.items()])
            )
            if kwargs
            else 'Executing command handler.',
        )
        return await resolve_function(handler, **kwargs)

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

    def _update_main_parser_description(self, parser: ArgumentParser, cmd: Command) -> None:
        router: Optional[str] = parser.prog
        if router and router != 'aiocli.commander':
            self._description.routers.setdefault(router, [])
            self._description.routers[router].append(cmd)
        else:
            self._description.default_router.append(cmd)
        self._parser.description = self._description.parse()

    def _update_parser_help(self, parser: ArgumentParser, prog: str) -> None:
        parser.usage = prog
        parser._positionals.title = '{0}Arguments{1}'.format(
            _yellow_color if self._color else '',
            _close_color if self._color else '',
        )
        parser._optionals.title = '{0}Options{1}'.format(
            _yellow_color if self._color else '',
            _close_color if self._color else '',
        )

    def _render_parser(self) -> None:
        cast(ApplicationHelpFormatter, self._parser.formatter_class).color = self._color
        self._description.color = self._color
        self._update_parser_help(self._parser, cast(str, self._parser.usage))
        self._parser.description = self._description.parse()
        for _, parser in self._parsers.items():
            parser.formatter_class = self._parser.formatter_class
            self._update_parser_help(parser, cast(str, parser.usage))

    def set_raw_input(self, *args, **kwargs) -> None:  # type: ignore
        self._raw_input = args, kwargs

    def get_raw_input(self) -> ApplicationRawInput:
        return self._raw_input

    def set_override_return(self, value: bool) -> None:
        self._override_return = value

    def get_override_return(self) -> bool:
        return self._override_return
