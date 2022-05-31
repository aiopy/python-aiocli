import asyncio
from functools import partial
from sys import version_info
from typing import Any, Callable, Optional, Set


def all_tasks(loop: Optional[asyncio.AbstractEventLoop] = None) -> Set["asyncio.Task[Any]"]:
    tasks = list(getattr(asyncio.Task, 'all_tasks')(loop))
    return {t for t in tasks if not t.done()}


if version_info >= (3, 7):
    all_tasks = getattr(asyncio, 'all_tasks')


def iscoroutinefunction(func: Callable[..., Any]) -> bool:
    while isinstance(func, partial):
        func = func.func
    return asyncio.iscoroutinefunction(func)


if version_info >= (3, 8):
    iscoroutinefunction = asyncio.iscoroutinefunction


async def resolve_function(func: Callable[..., Any], *args, **kwargs) -> Any:  # type: ignore
    if iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)
