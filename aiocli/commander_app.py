from argparse import ArgumentParser, RawTextHelpFormatter
from typing import List, Awaitable, Dict, Tuple, Optional, Any, Callable, NamedTuple, Coroutine

from typing_extensions import Protocol

__all__ = (
    # commander_app
    'Command',
    'command',
    'CommandHandler',
    'Application',
)


class CommandHandler(Protocol):
    def __call__(self, args: Dict[str, Any]) -> Coroutine[Any, Any, int]: ...


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


AppSignal = Callable[['Application'], Awaitable[None]]


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
    ) -> None:
        self._parser = ArgumentParser(
            description=description,
            prog=name,
            formatter_class=RawTextHelpFormatter,
        )
        self._parsers = {}
        self._commands = {}
        self.add_commands(commands or [])
        self._exit_code = 0
        self._on_startup = []
        self._on_shutdown = []
        self._on_cleanup = []

    async def __call__(self, args: List[str]) -> int:
        command_name = args[0] if len(args) > 0 else None
        if command_name not in self._parsers:
            self._parser.print_help()
            return 0
        namespace = self._parsers[command_name].parse_args(args[1:])
        self._exit_code = await self._commands[command_name].handler(vars(namespace))
        return self._exit_code

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
        self._parser.description = '{0}{1}\n'.format(self._parser.description, cmd.name)

    async def _execute_app_signals(self, app_signals: List[AppSignal]) -> None:
        _ = [await app_signal(self) for app_signal in app_signals]
