from argparse import ArgumentParser, RawTextHelpFormatter
from asyncio import iscoroutinefunction
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, NamedTuple, Optional, Tuple, Union

__all__ = (
    # commander_app
    'Command',
    'command',
    'CommandHandler',
    'Application',
)

CommandHandler = Callable[[Dict[str, Any]], Union[Callable[[Any], int], Coroutine[Any, Any, int]]]


class Command(NamedTuple):
    name: str
    handler: CommandHandler
    positionals: List[Tuple[str, Dict[str, Any]]]
    optionals: List[Tuple[str, Dict[str, Any]]]


def command(
    name: str,
    handler: CommandHandler,
    positionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    optionals: Optional[List[Tuple[str, Dict[str, Any]]]] = None
) -> Command:
    return Command(name=name, handler=handler, positionals=positionals or [], optionals=optionals or [])


AppSignal = Callable[['Application'], Union[None, Awaitable[None]]]


class Application:
    _parser: ArgumentParser
    _parsers: Dict[str, ArgumentParser]
    _commands: Dict[str, Command]
    _exit_code: int
    _on_startup: List[AppSignal]
    _on_shutdown: List[AppSignal]
    _on_cleanup: List[AppSignal]

    def __init__(
        self,
        commands: Optional[List[Command]] = None,
        *,
        name: str = 'aiocli.commander',
        description: str = '',
        version: str = 'unknown',
        on_startup: Optional[List[AppSignal]] = None,
        on_shutdown: Optional[List[AppSignal]] = None,
        on_cleanup: Optional[List[AppSignal]] = None,
    ) -> None:
        self._parser = ArgumentParser(
            description=description,
            prog=name,
            formatter_class=RawTextHelpFormatter,
        )
        self._parser.add_argument('--version', action='version', version=version)
        self._parsers = {}
        self._commands = {}
        self.add_commands(commands or [])
        self._exit_code = 0
        self._on_startup = on_startup if on_startup else []
        self._on_shutdown = on_shutdown if on_shutdown else []
        self._on_cleanup = on_cleanup if on_cleanup else []

    async def __call__(self, args: List[str]) -> int:
        command_name = args[0] if len(args) > 0 else None
        is_optional_argument = command_name and command_name[0] == '-'
        if command_name not in self._parsers and not is_optional_argument:
            self._parser.print_help()
            return 0
        if is_optional_argument:
            self._parser.parse_args()
            return 0
        namespace = self._parsers[command_name].parse_args(args[1:])
        handler = self._commands[command_name].handler
        self._exit_code = await handler(vars(namespace)) if iscoroutinefunction(handler) else handler(vars(namespace))
        return self._exit_code

    def include_router(self, router: 'Application') -> None:
        for name, cmd in router._commands.items():
            self._commands[name] = cmd
            self._parsers[name] = router._parsers[name]
            self._update_parser_description(name)
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
    ) -> Callable[[CommandHandler], CommandHandler]:
        def decorator(handler: CommandHandler) -> CommandHandler:
            self._add_command(Command(
                name=name,
                handler=handler,
                positionals=positionals or [],
                optionals=optionals or [],
            ))
            return handler

        return decorator

    def add_commands(self, commands: List[Command]) -> None:
        for cmd in commands:
            self._add_command(cmd)

    def get_command(self, name: str) -> Optional[Command]:
        return self._commands.get(name, None)

    @property
    def parser(self) -> ArgumentParser:
        return self._parser

    @property
    def exit_code(self) -> int:
        return self._exit_code

    @property
    def on_startup(self) -> List[AppSignal]:
        return self._on_startup

    async def startup(self) -> None:
        await self._execute_app_signals(self.on_startup)

    @property
    def on_shutdown(self) -> List[AppSignal]:
        return self._on_shutdown

    async def shutdown(self) -> None:
        await self._execute_app_signals(self._on_shutdown)

    @property
    def on_cleanup(self) -> List[AppSignal]:
        return self._on_cleanup

    async def cleanup(self) -> None:
        await self._execute_app_signals(self._on_cleanup)

    def _add_command(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd
        parser = ArgumentParser(prog=cmd.name)
        _ = [parser.add_argument(arg[0], **arg[1]) for arg in cmd.positionals + cmd.optionals]
        self._parsers[cmd.name] = parser
        self._update_parser_description(cmd.name)

    async def _execute_app_signals(self, app_signals: List[AppSignal]) -> None:
        for app_signal in app_signals:
            await app_signal(self) if iscoroutinefunction(app_signal) else app_signal(self)

    def _update_parser_description(self, name: str) -> None:
        self._parser.description = '{0}{1}\n'.format(self._parser.description, name)
