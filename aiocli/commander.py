import asyncio
import signal
import sys
from asyncio import gather, get_event_loop, iscoroutine
from asyncio.events import AbstractEventLoop
from typing import Any, Awaitable, Callable, List, Optional, Set, Union, cast

from aiocli.commander_app import Application, Command, Depends, command

__all__ = (
    # commander_app
    'Application',
    'Command',
    'command',
    'Depends',
    # commander
    'run_app',
    'ApplicationParser',
    'ApplicationReturn',
)

from aiocli.helpers import all_tasks


class GracefulExit(SystemExit):
    code = 0


def _raise_graceful_exit() -> None:
    raise GracefulExit()


def _cancel_tasks(to_cancel: Set['asyncio.Task[Any]'], loop: AbstractEventLoop) -> None:
    if not to_cancel:
        return
    for task in to_cancel:
        task.cancel()
    loop.run_until_complete(gather(*to_cancel, loop=loop, return_exceptions=True))
    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    'message': 'unhandled exception during asyncio.run() shutdown',
                    'exception': task.exception(),
                    'task': task,
                }
            )


class AppRunner:
    __slots__ = ('_app', '_loop', '_handle_signals', '_exit_code')

    def __init__(
        self,
        app: Application,
        *,
        loop: Optional[AbstractEventLoop] = None,
        handle_signals: bool = False,
        exit_code: bool = False
    ) -> None:
        self._app = app
        self._loop = loop or get_event_loop()
        self._handle_signals = handle_signals
        self._exit_code = exit_code

    @property
    def app(self) -> Application:
        return self._app

    async def setup(self) -> None:
        if self._handle_signals:
            try:
                self._loop.add_signal_handler(signal.SIGINT, _raise_graceful_exit)
                self._loop.add_signal_handler(signal.SIGTERM, _raise_graceful_exit)
            except NotImplementedError:  # pragma: no cover
                # add_signal_handler is not implemented on Windows
                pass
        await self.startup()

    async def startup(self) -> None:
        await self._app.startup()

    async def shutdown(self) -> None:
        await self._app.shutdown()

    async def cleanup(self) -> None:
        await self.shutdown()
        if self._handle_signals:
            try:
                self._loop.remove_signal_handler(signal.SIGINT)
                self._loop.remove_signal_handler(signal.SIGTERM)
            except NotImplementedError:  # pragma: no cover
                # remove_signal_handler is not implemented on Windows
                pass
        await self._app.cleanup()
        if self._exit_code:
            self._app.exit()


async def _run_app(
    app: Union[Application, Awaitable[Application]],
    *,
    loop: AbstractEventLoop,
    handle_signals: bool = True,
    argv: Optional[List[str]] = None,
    exit_code: bool = True
) -> None:
    app = cast(Application, await app if iscoroutine(app) else app)  # type: ignore
    runner = AppRunner(app, loop=loop, handle_signals=handle_signals, exit_code=exit_code)
    await runner.setup()
    try:
        await app(argv or sys.argv[1:])
    finally:
        await runner.cleanup()


ApplicationParser = Callable[..., Optional[List[str]]]

ApplicationReturn = Union[int, None, Callable[..., Optional[int]]]


def run_app(
    app: Union[Application, Awaitable[Application]],
    *,
    loop: Optional[AbstractEventLoop] = None,
    handle_signals: bool = True,
    argv: Optional[List[str]] = None,
    exit_code: bool = True,
    close_loop: bool = True,
    parser: Optional[ApplicationParser] = None
) -> ApplicationReturn:
    def wrapper(*args, **kwargs) -> Optional[int]:  # type: ignore
        loop_ = loop or get_event_loop()
        try:
            loop_.run_until_complete(
                _run_app(
                    app,
                    loop=loop_,
                    handle_signals=handle_signals,
                    argv=argv if parser is None else parser(*args, **kwargs),
                    exit_code=exit_code,
                )
            )
        except (GracefulExit, KeyboardInterrupt):  # pragma: no cover
            pass
        finally:
            if not loop_.is_closed():
                _cancel_tasks(to_cancel=all_tasks(loop=loop_), loop=loop_)
            if not loop_.is_closed():
                loop_.run_until_complete(loop_.shutdown_asyncgens())
            if close_loop and not loop_.is_closed():
                loop_.close()
        return cast(Application, app).exit_code

    return wrapper() if parser is None else wrapper
