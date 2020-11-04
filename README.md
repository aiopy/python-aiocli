# Async cli client/commander framework

aiocli is a Python library for simple and lightweight async console runner.

Full compatibility with argparse module and highly inspired by aiohttp module.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install aiocli.

```bash
pip install aiocli
```

## Usage

```python
# examples/commander.py
from aiocli import commander

app = commander.Application()

@app.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
async def handle(args: dict) -> int:
    print('Hello ' + args.get('name'))
    return 0

if __name__ == '__main__':
    commander.run_app(app)
```

## Requirements

- Python >= 3.6

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://github.com/ticdenis/python-aiocli/blob/master/LICENSE)
