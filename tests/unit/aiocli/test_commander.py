from asyncio import AbstractEventLoop
from platform import system
from typing import Optional
from unittest.mock import Mock

import pytest

# noinspection PyProtectedMembers
from aiocli.commander import AppRunner, GracefulExit, _raise_graceful_exit
from aiocli.commander_app import Application
from tests.conftest import amock


def test_graceful_exit_exception_has_code_0() -> None:
    assert GracefulExit().code == 0


@pytest.mark.asyncio
async def test_app_runner_setup_and_cleanup(event_loop: AbstractEventLoop) -> None:
    application_mock = amock(Application, ['startup', 'shutdown', 'cleanup', 'exit'])
    application_mock.startup.return_value = None
    application_mock.shutdown.return_value = None
    application_mock.cleanup.return_value = None
    exit_mock = Mock()
    exit_mock.side_effect = _raise_graceful_exit
    application_mock.exit = exit_mock

    runner = AppRunner(
        app=application_mock,
        loop=event_loop,
        handle_signals=system() != 'Windows',
        exit_code=True,
    )

    await runner.setup()
    assert len(event_loop.__dict__.get('_signal_handlers')) == 2
    application_mock.startup.assert_called_once()

    error_code: Optional[int] = None
    try:
        await runner.cleanup()
    except SystemExit as err:
        error_code = err.code
    finally:
        assert len(event_loop.__dict__.get('_signal_handlers')) == 0
        application_mock.shutdown.assert_called_once()
        application_mock.cleanup.assert_called_once()
        application_mock.exit.assert_called_once()
        assert error_code == 0
