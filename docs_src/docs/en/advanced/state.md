> The State in `aiocli` allows us to keep our dependencies in the application and modify it (if necessary) wherever we want.

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
