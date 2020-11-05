import sys
from asyncio import AbstractEventLoop, get_event_loop_policy
from typing import List, Optional, Union
from unittest.mock import MagicMock, Mock, patch

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)


from nest_asyncio import apply
from pytest import fixture

apply()


@fixture(scope='session')
def event_loop() -> AbstractEventLoop:
    return get_event_loop_policy().new_event_loop()


def amock(target: Union[str, object], attributes: Optional[List[str]] = None) -> Mock:
    target_async_mock = AsyncMock()
    if not attributes:
        patch(
            target=f'{target.__module__}.{target.__name__}' if isinstance(target, object) else target,  # type: ignore
            side_effect=target_async_mock,
        )
        return target_async_mock
    for attribute in attributes:
        attribute_async_mock = AsyncMock()
        patch.object(
            target=target,
            attribute=attribute,
            side_effect=attribute_async_mock,
        )
        target_async_mock[attribute] = attribute_async_mock
    return target_async_mock
