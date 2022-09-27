import asyncio
import signal
import sys
from asyncio import gather, get_event_loop
from asyncio.events import AbstractEventLoop
from typing import Any, Callable, List, Optional, Set, Union

from aiocli.commander_app import (
    Application,
    Command,
    CommandArgument,
    Depends,
    State,
    command,
)

__all__ = (
    # commander_app
    'State',
    'Depends',
    'CommandArgument',
    'Command',
    'command',
    'Application',
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
    loop.run_until_complete(gather(*to_cancel, return_exceptions=True))
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
        exit_code: bool = False,
    ) -> None:
        self._app = app
        self._loop = loop or get_event_loop()
        self._handle_signals = handle_signals
        self._exit_code = exit_code

    @property
    def app(self) -> Application:
        return self._app

    async def setup(self, all_hooks: bool = True) -> None:
        if self._handle_signals:
            try:
                self._loop.add_signal_handler(signal.SIGINT, _raise_graceful_exit)
                self._loop.add_signal_handler(signal.SIGTERM, _raise_graceful_exit)
            except NotImplementedError:  # pragma: no cover
                # add_signal_handler is not implemented on Windows
                pass
        await self.startup(all_hooks=all_hooks)

    async def startup(self, all_hooks: bool) -> None:
        await self._app.startup(all_hooks=all_hooks)

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
    app: Application,
    *,
    loop: AbstractEventLoop,
    handle_signals: bool = True,
    argv: Optional[List[str]] = None,
    exit_code: bool = True,
) -> None:
    runner = AppRunner(app, loop=loop, handle_signals=handle_signals, exit_code=exit_code)
    args = argv or sys.argv[1:]
    if app.should_ignore_hooks(args):
        await runner.setup(all_hooks=False)
        try:
            await app(args)
        finally:
            if exit_code:
                app.exit()
    else:
        await runner.setup(all_hooks=True)
        try:
            await app(args)
        finally:
            await runner.cleanup()


ApplicationParser = Callable[..., Optional[List[str]]]

ApplicationReturn = Union[int, None, Callable[..., Optional[int]]]


def run_app(
    app: Union[Application, Callable[[], Application]],
    *,
    loop: Optional[AbstractEventLoop] = None,
    handle_signals: bool = True,
    argv: Optional[List[str]] = None,
    exit_code: bool = True,
    close_loop: bool = True,
    parser: Optional[ApplicationParser] = None,
) -> ApplicationReturn:
    def wrapper(*args, **kwargs) -> Optional[int]:  # type: ignore
        loop_ = loop or get_event_loop()
        app_ = app if isinstance(app, Application) else app()
        try:
            loop_.run_until_complete(
                _run_app(
                    app_,
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
        return app_.exit_code

    return wrapper() if parser is None else wrapper
