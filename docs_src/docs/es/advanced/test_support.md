- Has utilizado el plugin [pytest-aiohttp](https://docs.aiohttp.org/en/stable/testing.html)? Esto está inspirado en ello.

```python
# code: python3 <file.py> <command> <positionals> <optionals>

from aiocli.commander import run_app, Application

app = Application(default_exit_code=1)

@app.command(name='greet:to', positionals=[('--name', {'default': 'World'})])
async def handle_greeting(name: str) -> int:
    print(f'Hello {name}')
    return 0

if __name__ == '__main__':
    run_app(app)

# test: pytest <test_file.py>

from aiocli.test_utils import TestClient, TestCommander
import pytest

@pytest.mark.asyncio
async def test_handle_greeting_command() -> None:
    commander = TestCommander(app)
    client = TestClient(commander)
    try:
        await commander.start_commander()
        args = 'greet:to --name aiocli'
        exit_code = await client.handle(
            args.split(' '),
            timeout=float(1),
            timeout_exit_code=134,
        )
        assert exit_code == 0
    finally:
        await commander.close()
```