from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from typing import List, Awaitable, Dict, Tuple, Optional, Any, Callable, NamedTuple, Coroutine, final

from typing_extensions import Protocol


class CommandHandler(Protocol):
    def __call__(self, args: Dict[str, Any]) -> Coroutine[Any, Any, int]: ...


class Command(NamedTuple):
    name: str
    handler: CommandHandler
    positionals: List[Tuple[str, Dict[str, Any]]]
    optionals: List[Tuple[str, Dict[str, Any]]]


AppSignal = Callable[['Application'], Awaitable[None]]


@final
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
            commands: List[Command],
            *,
            name: str = 'aiocli.commander',
            description: str = '',
    ) -> None:
        self._parser = ArgumentParser(
            description=description,
            prog=name,
            formatter_class=RawTextHelpFormatter
        )
        self._parsers = {}
        self._commands = {}
        for command in commands:
            self._add_command(command)
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

    def _add_command(self, command: Command) -> None:
        self._commands[command.name] = command
        parser = ArgumentParser(prog=command.name)
        _ = [parser.add_argument(arg[0], **arg[1]) for arg in command.positionals + command.optionals]
        self._parsers[command.name] = parser
        self._parser.description = f'{self._parser.description}{command.name}\n'

    async def _execute_app_signals(self, app_signals: List[AppSignal]) -> None:
        _ = [await app_signal(self) for app_signal in app_signals]
