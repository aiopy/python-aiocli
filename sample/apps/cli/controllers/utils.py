from logging import StreamHandler, getLogger, Logger

from aiocli.commander_app import State


def get_logger(state: State) -> Logger:
    logger = getLogger(state.get('envs')['LOGGER_NAME'])
    logger.setLevel(state.get('envs')['LOGGER_LEVEL'])
    handler = StreamHandler()
    logger.addHandler(handler)
    return logger
