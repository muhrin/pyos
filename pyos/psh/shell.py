import logging
import sys
from typing import List

import stevedore

from . import base

__all__ = ('PyosShell',)

PLUGINS_COMMANDS_NS = 'pyos.plugins.shell'


class PyosShell(base.BaseShell):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__()
        for cmd_set in plugins_get_commands():
            self.install_command_set(cmd_set)


logger = logging.getLogger(__name__)


def plugins_get_commands() -> List:
    """Get all mincepy types and type helper instances registered as extensions"""
    mgr = stevedore.extension.ExtensionManager(
        namespace=PLUGINS_COMMANDS_NS,
        invoke_on_load=False,
    )

    commands = []

    def get_command(extension: stevedore.extension.Extension):
        try:
            commands.extend(extension.plugin())
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to get command plugin from %s", extension.name)

    try:
        mgr.map(get_command)
    except stevedore.extension.NoMatches:
        pass

    return commands


if __name__ == '__main__':
    app = PyosShell()
    sys.exit(app.cmdloop())
