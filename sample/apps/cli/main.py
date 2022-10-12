from os import environ

from aiocli.commander import run_app
from aiocli.commander_app import Application
from sample.apps.cli.controllers.calculator_router import calculator_router
from sample.apps.cli.controllers.shared_router import shared_router
from sample.apps.settings import container


def app() -> Application:
    return Application(
        debug=environ.get('DEBUG', '0') == 1,
        use_print_for_logging=environ.get('DEBUG', '0') == 1,
        title='aiocli.sample',
        description='The sample description',
        version='0.0.0',
        state=container,
        routers=[
            shared_router,
            calculator_router,
        ],
    )


def main() -> None:
    run_app(app=app)
