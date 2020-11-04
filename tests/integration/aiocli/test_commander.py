from platform import system
from typing import Optional

from aiocli.commander import run_app
from aiocli.commander_app import Application


def test_run_app() -> None:
    error_code: Optional[int] = None
    try:
        app = Application()

        @app.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
        def handle(args: dict) -> int:
            return 0 if args['name'] == 'test' else 1

        run_app(
            app=app,
            loop=None,
            handle_signals=system() != 'Windows',
            argv=['greet:to', '--name', 'test'],
            exit_code=True,
        )
    except SystemExit as err:
        error_code = err.code
    finally:
        assert error_code == 0
