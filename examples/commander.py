from aiocli import commander

app = commander.Application()


@app.command(name='greet:to', positionals=[('--name', {'default': 'World!'})])
async def handle(args: dict) -> int:
    print('Hello ' + args.get('name'))
    return 0


# python3 commander.py <command> <positionals> <optionals>
if __name__ == '__main__':
    commander.run_app(app)
