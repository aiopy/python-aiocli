# AIOCLI

Un moderno ligero ejecutor de consola asíncrono para construir CLIs con Python 3.10+ basado en el módulo estándar de Python [argparse](https://docs.python.org/3/library/argparse.html) y [type hints](https://docs.python.org/3/library/typing.html) altamente inspirado en [AIOHTTP](https://github.com/aio-libs/aiohttp) y [FastApi](https://github.com/tiangolo/fastapi).

Características principales:

* **Integración nativa**: Basado en (y totalmente compatible con) el módulo argparse de Python.
* **Soporte asíncrono**: Maneja comandos a/síncronamente para cualquier tipo de aplicación.
* **Soporte serverless**: Integracion con *AWS Lambda*, *Azure Function* y *Google Cloud Function*.
* **Soporte para tests**: Diseñado para ser fácil de ejecutar y probar.

## Requisitos

- Python 3.10+

## Instalación

```shell
python3 -m pip install aiocli
```

## Ejemplo

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

## Licencia

[MIT](https://github.com/aiopy/python-aiocli/blob/master/LICENSE)
