# -*- coding: utf-8 -*-
"""Print working directory command"""
import argparse
import logging
from typing import Union

import cmd2


class Log(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('logger',
                        help='the logger to set loglevel for, can be empty string for root')
    parser.add_argument('level', help='the log level to set')

    @cmd2.with_argparser(parser)
    def do_log(self, args):

        if isinstance(args.level, int):
            level = args.level
        else:
            level = logging.getLevelName(args.level)

        set_logging(args.logger, level)
        print(f"Log level for '{args.logger}' set to {args.level}")


def set_logging(logger: str, level: Union[int, str]):
    log = logging.getLogger(logger)
    log.setLevel(level)

    formatter = logging.Formatter('%(levelname)s: %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    log.addHandler(handler)
