from asyncio import get_event_loop_policy, iscoroutinefunction
from typing import Any, Callable, Coroutine

__all__ = (
    # helpers
    'resolve_function',
    'resolve_coroutine',
)


async def resolve_function(func: Callable[..., Any], *args, **kwargs) -> Any:  # type: ignore
    if iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)


def resolve_coroutine(func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:  # type: ignore
    return get_event_loop_policy().get_event_loop().run_until_complete(func(*args, **kwargs))
