# Async cli client/commander framework

aiocli is a Python library for simple and lightweight async console runner.

Full compatibility with argparse module and highly inspired by aiohttp module.

## Installation

Use the package manager [pip](https://pypi.org/project/aiocli/) to install aiocli.

```bash
pip install aiocli
```

## Usage

```python
# examples/commander.py
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
```

## Requirements

- Python >= 3.6

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://github.com/ticdenis/python-aiocli/blob/master/LICENSE)
