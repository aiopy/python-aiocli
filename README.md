# Async cli client/commander framework

[![PyPI version](https://badge.fury.io/py/aiocli.svg)](https://badge.fury.io/py/aiocli)
[![PyPIDownloads](https://static.pepy.tech/badge/aiocli)](https://pepy.tech/project/aiocli)
[![CI](https://github.com/aiopy/python-aiocli/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aiopy/python-aiocli/actions/workflows/ci.yml)

aiocli is a Python library for simple and lightweight async console runner.

Full compatibility with argparse module and highly inspired by aiohttp module.

## Installation

Use the package manager [pip](https://pypi.org/project/aiocli/) to install aiocli.

```bash
pip install aiocli
```

## Documentation

- Visit [aiocli docs](https://aiopy.github.io/python-aiocli/).

## Usage

```python
from logging import getLogger, Logger, StreamHandler
from os import getenv

from aiocli.commander import run_app, Application, Depends, State

app = Application(state={
    'envs': {
        'LOGGER_NAME': str(getenv('LOGGER_NAME', 'example_app')),
        'LOGGER_LEVEL': str(getenv('LOGGER_LEVEL', 'INFO')),
    }
})

def _get_logger(state: State) -> Logger:
    logger = getLogger(state.get('envs')['LOGGER_NAME'])
    logger.setLevel(state.get('envs')['LOGGER_LEVEL'])
    handler = StreamHandler()
    logger.addHandler(handler)
    return logger

@app.command(name='greet:to', positionals=[('name', {'default': 'World!'})])
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

## Requirements

- Python >= 3.10

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://github.com/aiopy/python-aiocli/blob/master/LICENSE)
