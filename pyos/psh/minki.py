import minkipy

import argparse

import cmd2

parser = argparse.ArgumentParser()  # pylint: disable=invalid-name
parser.add_argument('project', nargs=1, type=str)


@cmd2.with_argparser(parser)
def do_workon(app: cmd2.Cmd, args):
    try:
        project = minkipy.workon(args.project[0])
    except ValueError as exc:
        app.perror(exc)
    else:
        app.poutput("Switched to '{}'".format(project))
