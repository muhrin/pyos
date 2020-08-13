"""Print working directory command"""
import argparse
import logging
from typing import Union

import cmd2


class Log(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('logger',
                        help='the logger to set loglevel for, can be empty string for root')
    parser.add_argument('level', help="the log level to set")

    @cmd2.with_argparser(parser)
    def do_log(self, args):  # pylint: disable=no-self-use

        if isinstance(args.level, int):
            level = args.level
        else:
            level = logging.getLevelName(args.level)

        set_logging(args.logger, level)
        print("Log level for '{}' set to {}".format(args.logger, args.level))


def set_logging(logger: str, level: Union[int, str]):
    log = logging.getLogger(logger)
    log.setLevel(level)

    formatter = logging.Formatter('%(levelname)s: %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    log.addHandler(handler)
