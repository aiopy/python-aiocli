> One way to control the exceptions that occur to avoid unexpected behaviour and map your exits codes is to use exception handlers that work on a per type basis.

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
