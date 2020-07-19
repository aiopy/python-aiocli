# Async Python application

aiocli is a Python library for simple and lightweight async console runner.

Full compatibility with argparse module and highly inspired by aiohttp module.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install aiocli.

```bash
pip install aiocli
```

## Usage

```python
from asyncio import get_event_loop, AbstractEventLoop
from pyaioapp import AsyncApplication
from aiocli.commander import Application, run_app, Command
from typing import Dict as Container, Any

SETTINGS = {
    'DEBUG': '0', 'DEBUG_HOST': '0.0.0.0', 'DEBUG_PORT': '5678'
}


async def get_container(settings: dict, **kwargs) -> Container:
    async def hello_world_command(args: dict) -> int:
        print(f'Hello {args.get("name")}!')
        return 0

    return {
        'hello_world_command': hello_world_command
    }


async def get_runner(container: Container) -> Application:
    return Application([
        Command(
            name='hello:world',
            handler=container.get('hello_world_command'),
            optionals=[('--name', {'default': 'World'})],
            positionals=[]
        ),
    ])


class CliApp(AsyncApplication[Container, Application]):
    async def __aenter__(self) -> Application:
        self._container = await get_container(SETTINGS, loop=self.loop)
        self._runner = await get_runner(self._container)
        return self._runner

    def __call__(self) -> None:
        run_app(app=self.__aenter__(), loop=self.loop)


def main(loop: AbstractEventLoop) -> Any:
    if SETTINGS['DEBUG'] == '1':
        from ptvsd import enable_attach  # type: ignore
        enable_attach(
            address=(SETTINGS['DEBUG_HOST'], int(SETTINGS['DEBUG_PORT']))
        )
    return CliApp(loop).__call__()


if __name__ == '__main__':
    main(get_event_loop())
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://github.com/ticdenis/python-aiocli/blob/master/LICENSE)
