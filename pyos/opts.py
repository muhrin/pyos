import typing


class Op:
    """A simple option, acts as a flag (it's presence means True)"""

    def __init__(self, name: str):
        self._name = name

    def __str__(self):
        return self._name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Op):
            return False

        return self.name == other.name

    @property
    def name(self):
        return self._name

    def __call__(self, val):
        """Promote to a value option"""
        op = ValueOp(self.name, val)
        return op

    def __neg__(self):
        """Enable the familiar command line -[op] notation, e.g. -l.
        This also allows for double negation i.e. --l"""
        return self


class ValueOp(Op):
    """An operator that has a value"""

    def __init__(self, name: str, val: typing.Any = None):
        super().__init__(name)
        self._val = val

    def __eq__(self, other) -> bool:
        if not super().__eq__(other):
            return True

        return self.val == other.val

    @property
    def val(self):
        return self._val


def separate_opts(*args):
    """Separate out the options from the other arguments"""
    opts = []
    rest = []
    for arg in args:
        if isinstance(arg, Op):
            opts.append(arg)
        else:
            rest.append(arg)
    return opts, rest


def extract(opt: Op, opts: list) -> False:
    try:
        opts.remove(opt)
        return True
    except ValueError:
        return False


def extract_val(opt: Op, opts: list, *args):
    assert len(args) < 2, "Can only supply one default value"
    try:
        return opts.pop(opts.index(opt)).val
    except ValueError:
        if args:
            return args[0]

        raise
