import sys
from asyncio import AbstractEventLoop, TimeoutError, get_event_loop, wait_for
from types import TracebackType
from typing import Any, Callable, List, Optional, Type, Union

from aiocli.commander import AppRunner
from aiocli.commander_app import Application


class TestCommander:
    __test__ = False
    _app: Application
    _loop: AbstractEventLoop
    _runner: Optional[AppRunner]
    _all_hooks: bool
    _ignore_internal_hooks: bool

    def __init__(
        self,
        app: Union[Application, Callable[[], Application]],
        *,
        loop: Optional[AbstractEventLoop] = None,
        all_hooks: bool = True,
        ignore_internal_hooks: bool = False,
    ) -> None:
        self._app = app if isinstance(app, Application) else app()
        self._loop = loop or get_event_loop()
        self._runner = None
        self._all_hooks = all_hooks
        self._ignore_internal_hooks = ignore_internal_hooks

    async def handle(
        self,
        argv: Optional[List[str]] = None,
        *,
        timeout: Optional[float] = None,
        timeout_exit_code: Optional[int] = None,
    ) -> int:
        try:
            await wait_for(self._app(argv or sys.argv[1:]), timeout=timeout)
        except TimeoutError:
            if timeout_exit_code is not None:
                return timeout_exit_code
        return int(self._app.exit_code)

    async def start_commander(self, **kwargs: Any) -> None:
        if self._runner:
            return
        self._runner = await self._make_runner(**kwargs)
        await self._runner.setup(all_hooks=self._all_hooks, ignore_internal_hooks=self._ignore_internal_hooks)

    async def __aenter__(self) -> 'TestCommander':
        await self.start_commander(all_hooks=self._all_hooks, ignore_internal_hooks=self._ignore_internal_hooks)
        return self

    async def close(self) -> None:
        if self._runner:
            await self._runner.cleanup(all_hooks=self._all_hooks, ignore_internal_hooks=self._ignore_internal_hooks)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def _make_runner(self, **kwargs: Any) -> AppRunner:
        return AppRunner(self._app, loop=self._loop, **kwargs)


class TestClient:
    __test__ = False
    _commander: TestCommander

    def __init__(self, commander: TestCommander) -> None:
        self._commander = commander

    async def handle(
        self,
        argv: Optional[List[str]] = None,
        *,
        timeout: Optional[float] = None,
        timeout_exit_code: Optional[int] = 1,
    ) -> int:
        return await self._commander.handle(argv, timeout=timeout, timeout_exit_code=timeout_exit_code)

    async def start_commander(self) -> None:
        await self._commander.start_commander()

    async def __aenter__(self) -> 'TestClient':
        await self.start_commander()
        return self

    async def close(self) -> None:
        await self._commander.close()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()
