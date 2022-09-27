import asyncio
from asyncio import get_event_loop_policy
from functools import partial
from sys import version_info
from typing import Any, Callable, Coroutine, Optional, Set

__all__ = (
    # helpers
    'all_tasks',
    'iscoroutinefunction',
    'resolve_function',
    'resolve_coroutine',
)


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


def resolve_coroutine(func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:  # type: ignore
    return get_event_loop_policy().get_event_loop().run_until_complete(func(*args, **kwargs))
