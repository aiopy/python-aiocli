> Una manera de controlar las excepciones que se producen para evitar comportamientos inesperados y mapear tus exits codes es utilizando los exception handler que funcionan tanto por tipo.

```python
from typing import Dict, Any

from aiocli.commander import Application, run_app
from aiocli.commander_app import Command

app = Application(state={'hello': 'world'})


@app.exception_handler(typ=BaseException)
async def log_exception_handler(err: BaseException, cmd: Command, args: Dict[str, Any]) -> int:
    print(f'Command: {cmd.name} Err: {err}')
    return 1


@app.command(name='foo')
async def bad_handler() -> int:
    raise Exception('Oh no!')


if __name__ == '__main__':
    run_app(app, argv=['foo'])
```
