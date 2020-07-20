from aiocli import commander


async def handle(args: dict) -> int:
    print('Hello ' + args.get('name'))
    return 0


app = commander.Application()
app.add_commands([commander.command('greet:to', handle, [('--name', {'default': 'World!'})])])

# python commander.py <command> <positionals> <optionals>
if __name__ == '__main__':
    commander.run_app(app)
