> El State en `aiocli` nos permite mantener nuestras dependencias en la aplicación y modificarlo (si es necesario) dónde queramos.

```python
from aiocli.commander import Application, run_app
from aiocli.commander_app import State

app = Application(state={'hello': 'world'})


@app.command(name='show:state')
async def handle_show_state(state: State) -> int:
    print(state)
    return 0


if __name__ == '__main__':
    run_app(app, argv=['show:state'])
```
