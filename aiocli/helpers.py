import asyncio
import functools
import sys
from typing import Any, Callable, Optional, Set


def all_tasks(loop: Optional[asyncio.AbstractEventLoop] = None) -> Set["asyncio.Task[Any]"]:
    tasks = list(asyncio.Task.all_tasks(loop))
    return {t for t in tasks if not t.done()}


if sys.version_info >= (3, 7):
    all_tasks = getattr(asyncio, 'all_tasks')


def iscoroutinefunction(func: Callable[..., Any]) -> bool:
    while isinstance(func, functools.partial):
        func = func.func
    return asyncio.iscoroutinefunction(func)


if sys.version_info >= (3, 8):
    iscoroutinefunction = asyncio.iscoroutinefunction
