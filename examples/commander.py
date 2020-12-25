from functools import lru_cache
from logging import getLogger, Logger, StreamHandler, Formatter
from os import getenv
from typing import Dict, Any

from aiocli import commander

app = commander.Application()


@lru_cache
def _get_envs() -> Dict[str, Any]:
    return {
        'LOGGER_NAME': getenv('LOGGER_NAME', 'example_commander'),
        'LOGGER_LEVEL': getenv('LOGGER_LEVEL', 'INFO'),
        'LOGGER_FORMAT': getenv('LOGGER_FORMAT', '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')
    }


def _get_logger(envs: Dict[str, Any] = commander.Depends(_get_envs)) -> Logger:
    logger = getLogger(envs['LOGGER_NAME'])
    logger.setLevel(envs['LOGGER_LEVEL'])
    handler = StreamHandler()
    handler.setLevel(envs['LOGGER_LEVEL'])
    formatter = Formatter(envs['LOGGER_FORMAT'])
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


@app.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
async def handle(name: str, logger: Logger = commander.Depends(_get_logger)) -> int:
    logger.info('Hello ' + name)
    return 0


# python3 commander.py <command> <positionals> <optionals>
if __name__ == '__main__':
    commander.run_app(app, argv=['greet:to', '--name', 'GitHub!'])
