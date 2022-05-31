from asyncio import AbstractEventLoop
from typing import List, Optional

from aiocli.commander import Application, ApplicationParser, ApplicationReturn, run_app

__all__ = (
    # commander
    'Application',
    'ApplicationParser',
    'ApplicationReturn',
    # commander_app_wrappers
    'aws_run_app',
    'az_run_app',
    'gcp_run_app',
    'alibaba_run_app',
    'oracle_run_app',
)


def _cloud_run_app(
    app: Application,
    *,
    loop: Optional[AbstractEventLoop] = None,
    handle_signals: bool = True,
    argv: Optional[List[str]] = None,
    exit_code: bool = False,
    close_loop: bool = False,
    parser: Optional[ApplicationParser] = None
) -> ApplicationReturn:
    return run_app(
        app=app,
        loop=loop,
        handle_signals=handle_signals,
        argv=argv,
        exit_code=exit_code,
        close_loop=close_loop,
        parser=(lambda *args, **kwargs: argv) if parser is None else parser,
    )


aws_run_app = _cloud_run_app
az_run_app = _cloud_run_app
gcp_run_app = _cloud_run_app
alibaba_run_app = _cloud_run_app
oracle_run_app = _cloud_run_app
