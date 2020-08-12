import ast
import collections
import functools
from typing import Callable

from pytray import obj_load
from mincepy import qops

__all__ = ('type_string',)


def type_string(value: str) -> type:
    """Helper to get types as an argparse parameter"""
    return obj_load.load_obj(value)


def parse_query(value: str) -> dict:
    for oper, func in OPERATORS.items():
        if oper in value:
            left, right = value.split(oper, maxsplit=1)

            # Try getting python types from the right hand side (e.g. None, False, 3, 2.6, etc)
            try:
                right = ast.literal_eval(right.rstrip())
            except ValueError:
                pass

            return func(left.strip(), right)

    raise ValueError("Unknown condition: {}".format(value))


def apply(operator: Callable, name: str, value):
    return {name: operator(value)}


def _new(operator: Callable):
    return functools.partial(apply, operator)


OPERATORS = collections.OrderedDict([
    ('!=', _new(qops.ne_)),
    ('=', _new(lambda x: x)),
    ('>', _new(qops.gt_)),
    ('<', _new(qops.lt_)),
])
