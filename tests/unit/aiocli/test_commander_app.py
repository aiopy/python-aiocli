from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest

from aiocli.commander_app import Application, Command, command


def test_application_include_router() -> None:
    root_hooks = {
        'on_startup': [Mock()],
        'on_shutdown': [Mock()],
        'on_cleanup': [Mock()],
    }
    app = Application(title='root', **root_hooks)

    @app.command(name='one-of-root')
    def handle(_: dict) -> int:
        return 0

    router_hooks = {
        'on_startup': [Mock()],
        'on_shutdown': [Mock()],
        'on_cleanup': [Mock()],
    }
    router = Application(title='child', **router_hooks)

    @router.command(name='one-of-child')
    def handle(_: dict) -> int:
        return 0

    app.include_router(router=router)

    assert app.get_command(name='one-of-root')
    assert app.get_command(name='one-of-child')

    assert app.on_startup[0] is root_hooks['on_startup'][0]
    assert app.on_startup[1] is router_hooks['on_startup'][0]
    assert app.on_shutdown[0] is root_hooks['on_shutdown'][0]
    assert app.on_shutdown[1] is router_hooks['on_shutdown'][0]
    assert app.on_cleanup[0] is root_hooks['on_cleanup'][0]
    assert app.on_cleanup[1] is router_hooks['on_cleanup'][0]


def test_application_add_commands() -> None:
    app = Application()
    command_ = command(name='test', handler=lambda _: 0)
    app.add_commands([command_])
    assert app.get_command(name=command_.name)


@pytest.mark.asyncio
async def test_application_startup() -> None:
    on_startup_mock = Mock()
    app = Application(on_startup=[on_startup_mock])
    await app.startup()
    on_startup_mock.assert_called_once()


@pytest.mark.asyncio
async def test_application_shutdown() -> None:
    on_shutdown_mock = Mock()
    app = Application(on_shutdown=[on_shutdown_mock])
    await app.shutdown()
    on_shutdown_mock.assert_called_once()


@pytest.mark.asyncio
async def test_application_cleanup() -> None:
    on_cleanup_mock = Mock()
    app = Application(on_cleanup=[on_cleanup_mock])
    await app.cleanup()
    on_cleanup_mock.assert_called_once()


def test_application_default_exit_code() -> None:
    assert Application().exit_code == 0


def test_application_specific_exit_code() -> None:
    assert Application(default_exit_code=1).exit_code == 1


@pytest.mark.asyncio
async def test_application_fails_when_command_not_found() -> None:
    with pytest.raises(ValueError):
        await Application().__call__([])


@pytest.mark.asyncio
@pytest.mark.parametrize('command_name', ['-h', '--help'])
async def test_application_print_help_and_return_exit_code_0_when_command_is(command_name: str) -> None:
    assert await Application().__call__([command_name]) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('command_name', ['--version'])
async def test_application_print_version_and_return_exit_code_0_when_command_is_(command_name: str) -> None:
    assert await Application().__call__([command_name]) == 0


@pytest.mark.asyncio
async def test_application_execute_async_command_and_return_exit_code_0() -> None:
    app = Application()

    @app.command(name='test')
    async def handle(_: dict) -> int:
        return 0

    assert await app.__call__(['test']) == 0


@pytest.mark.asyncio
async def test_application_execute_sync_command_and_return_exit_code_0() -> None:
    app = Application()

    @app.command(name='test')
    def handle(_: dict) -> int:
        return 0

    assert await app.__call__(['test']) == 0


@pytest.mark.asyncio
async def test_application_execute_exception_handler_and_return_specific_exit_code() -> None:
    app = Application()

    @app.exception_handler(typ=ValueError)
    def exception_handler(err: ValueError, cmd: Command, kwargs: Dict[str, Any]) -> Optional[int]:
        return 3

    @app.command(name='test')
    def handle() -> Optional[int]:
        raise ValueError('Test')

    assert await app.__call__(['test']) == 3
