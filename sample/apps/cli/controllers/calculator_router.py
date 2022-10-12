from logging import Logger

from aiocli.commander_app import Depends, Application
from sample.apps.cli.controllers.utils import get_logger

calculator_router = Application(title='calculator')


@calculator_router.command(
    name='div',
    description='Divide a between b',
    positionals=[('a', {'type': float}), ('b', {'type': float})],
)
async def handle_division(a: float, b: float, logger: Logger = Depends(get_logger)) -> int:
    try:
        logger.info(f'Result {a} / {b} = {(a / b)}')
        return 0
    except BaseException as err:
        logger.error(f'Error: {err}')
        return 1
