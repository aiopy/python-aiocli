> Los Hooks son una poderosa herramienta que permiten controlar el ciclo de vida de tu aplicación.

Hay 3 tipos de Hooks:

* `on_startup`: Donde inicializarás tus dependencias por ejemplo.
* `on_shutdown`: Donde cerrarás las conexiones por ejemplo.
* `on_cleanup`: Donde liberarás la memoria por ejemplo.

¡Los hooks internos siempre serán ejecutados aunque hayan sido ignorados en la definición del Command!

```python
from aiocli.commander import Application, run_app
from aiocli.commander_app import CommandArgument, State


class FakeDatabaseConnection:
    def open(self) -> None:
        pass

    def query(self, q: str) -> None:
        print(q)

    def close(self) -> None:
        pass


app = Application(state={'db': FakeDatabaseConnection()})


@app.on_startup.append
async def on_startup(app_: Application) -> None:
    app_.state['db'].open()


@app.on_shutdown.append
async def on_shutdown(app_: Application) -> None:
    app_.state['db'].close()


@app.on_cleanup.append
async def on_cleanup(app_: Application) -> None:
    app_.state['db'] = None


@app.command(name='greet:to', positionals=[CommandArgument(name_or_flags='--name')])
async def handle_show_greeting_query(name: str, state: State) -> int:
    state['db'].query(f'SELECT greeting from greetings WHERE name="{name}" LIMIT 1;')
    return 0


if __name__ == '__main__':
    run_app(app, argv=['greet:to', '--name', 'hook!'])
```
