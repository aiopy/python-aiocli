# AIOCLI

A modern, lightweight, async console runner for building CLIs with Python 3.6+ based on standard Python's [argparse module](https://docs.python.org/3/library/argparse.html) and [type hints](https://docs.python.org/3/library/typing.html) highly inspired by [AIOHTTP](https://github.com/aio-libs/aiohttp) and [FastApi](https://github.com/tiangolo/fastapi).

Key Features:

* **Native-based**: Based on (and fully compatible with) Python's argparse module.
* **Async support**: Handle commands completely async thinking in smaller and larger apps.
* **Serverless support**: Wrappers for *AWS Lambda*, *Azure Function* and *Google Cloud Function*.
* **Test support**: Designed to be easy to execute and test.

## Requirements

- Python 3.6+

## Installation

```shell
python3 -m pip install aiocli
```

## Example

```python hl_lines="6 37"
from logging import getLogger, Logger, StreamHandler
from os import getenv

from aiocli.commander import run_app, Application, Depends

app = Application()

def _get_envs() -> dict[str, str]:
    return {
        'LOGGER_NAME': str(getenv('LOGGER_NAME', 'example_app')),
        'LOGGER_LEVEL': str(getenv('LOGGER_LEVEL', 'INFO')),
    }

def _get_logger(envs: dict[str, str] = Depends(_get_envs)) -> Logger:
    logger = getLogger(envs['LOGGER_NAME'])
    logger.setLevel(envs['LOGGER_LEVEL'])
    handler = StreamHandler()
    logger.addHandler(handler)
    return logger

@app.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
async def handle_greeting(name: str, logger: Logger = Depends(_get_logger)) -> int:
    logger.info(f'Hello {name}')
    return 0

@app.command(name='div', optionals=[('--a', {'type': float}), ('--b', {'type': float})])
async def handle_division(a: float, b: float, logger: Logger = Depends(_get_logger)) -> int:
    try:
        logger.info(f'Result {a} / {b} = {(a / b)}')
        return 0
    except BaseException as err:
        logger.error(f'Error: {err}')
        return 1

# python3 main.py <command> <positionals> <optionals>
if __name__ == '__main__':
    run_app(app)
```

## License

[MIT](https://github.com/ticdenis/python-aiocli/blob/master/LICENSE)
