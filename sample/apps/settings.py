from os import getenv

from aiocli.commander_app import State


class ContainerState(State):
    pass


def container() -> ContainerState:
    return ContainerState({
        'envs': {
            'LOGGER_NAME': str(getenv('LOGGER_NAME', 'aiocli_sample')),
            'LOGGER_LEVEL': str(getenv('LOGGER_LEVEL', 'INFO')),
        }
    })
