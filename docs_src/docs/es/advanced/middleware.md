> Los middleware son un poderoso mecanismo que se ejecuta en secuencia antes del command handler permitiendo interceptar el comando y los argumentos ya resueltos.

```python
from datetime import datetime
from typing import Any, Dict

from aiocli.commander import Application, run_app
from aiocli.commander_app import Command, CommandArgument


def info_middleware(cmd: Command, args: Dict[str, Any]) -> None:
    print(f'Command: {cmd.name}  Arguments: {args}')


app = Application(middleware=[info_middleware])


@app.middleware()
async def time_middleware() -> None:
    print(f'Time: {datetime.now()}')


@app.command(name='greet:to', positionals=[CommandArgument(name_or_flags='--name')])
async def handle_greeting(name: str) -> int:
    print(f'Hello {name}')
    return 0


if __name__ == '__main__':
    run_app(app, argv=['greet:to', '--name', 'middleware!'])
```
