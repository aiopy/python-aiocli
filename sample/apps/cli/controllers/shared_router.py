from os import system

from aiocli.commander import Application
from aiocli.commander_app import CommandArgument

shared_router = Application()


@shared_router.command(
    name='eval',
    description='Command to evaluate directly on the system. Be very careful!',
    positionals=[
        CommandArgument(name_or_flags='command', type=str, help='The command to run wrapped in quotes'),
    ],
    ignore_hooks=True,
)
async def eval_command_handler(command: str) -> int:
    return system(command)  # nosec


@shared_router.command(
    name='serve',
    description='Run application on the Python development server',
    optionals=[
        CommandArgument(name_or_flags='--timeout', type=int, required=False, default=3600 * 8),
    ],
    ignore_hooks=True,
)
async def serve_command_handler(timeout: int) -> int:
    return 0


@shared_router.command(
    name='healthcheck',
    description='Check application health',
    optionals=[
        CommandArgument(name_or_flags='--fs-tmp', type=bool, nargs='?', const=True, default=True, required=False),
        CommandArgument(name_or_flags='--timeout', type=int, required=False, default=60),
        CommandArgument(name_or_flags='--wait', type=bool, nargs='?', const=True, required=False),
    ],
    ignore_hooks=True,
)
async def healthcheck_command_handler(
    fs_tmp: bool,
    timeout: int,
    wait: bool,
) -> int:
    return 0
