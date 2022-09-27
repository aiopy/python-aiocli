from platform import system
from typing import Any, Callable

import pytest

from aiocli.commander_app_wrappers import (
    Application,
    ApplicationParser,
    alibaba_run_app,
    aws_run_app,
    az_run_app,
    gcp_run_app,
    oracle_run_app,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'cloud_run_app',
    [
        aws_run_app,
        az_run_app,
        gcp_run_app,
        alibaba_run_app,
        oracle_run_app,
    ],
)
def test_cloud_run_app(cloud_run_app: Callable[..., Callable[..., int]]) -> None:
    def app() -> Application:
        sut = Application(default_exit_code=-1)

        @sut.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
        def handle(name: str) -> int:
            return 0 if name == 'test' else 1

        return sut

    def assert_exit_code_is_0(parser: ApplicationParser) -> None:
        assert (
            cloud_run_app(
                app=app,
                handle_signals=system() != 'Windows',
                parser=parser,
            )({'detail': ['greet:to', '--name', 'test']}, {})
            == 0
        )

    lambda_parser = lambda event_or_request_or_data, context: event_or_request_or_data['detail']

    assert_exit_code_is_0(parser=lambda_parser)

    def args_parser(event_or_request_or_data, context):
        return event_or_request_or_data['detail']

    assert_exit_code_is_0(parser=args_parser)

    def kwargs_parser(event_or_request_or_data: Any, context: Any) -> Any:
        return event_or_request_or_data['detail']

    assert_exit_code_is_0(parser=kwargs_parser)
