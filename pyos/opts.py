from typing import Iterable, Union


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

    def __neg__(self):
        """Enable the familiar command line -[op] notation, e.g. -l.
        This also allows for double negation i.e. --l"""
        return self


class ValueOp(Op):
    """An operator that has a value"""

    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        self._kwargs = kwargs

    def __eq__(self, other) -> bool:
        if not super().__eq__(other):
            return True

        try:
            return self.get() == other.get()
        except RuntimeError:
            return False

    def __call__(self, val):
        """pass in a value for this option"""
        if hasattr(self, '_val'):
            raise RuntimeError("Value already set!")
        op = ValueOp(self.name, **self._kwargs)
        setattr(op, '_val', val)
        return op

    @property
    def default(self):
        try:
            return self._kwargs['default']
        except KeyError:
            raise AttributeError('default')

    def has_default(self):
        return 'default' in self._kwargs

    def get(self, *args):
        if len(args) > 1:
            raise ValueError("Takes only one argument, a default value")

        try:
            return getattr(self, '_val')
        except AttributeError:
            pass

        # Look for a default
        if args:
            return args[0]

        try:
            return self._kwargs['default']
        except KeyError:
            pass

        raise ValueError("This option has no set value or default")


class Flag(ValueOp):

    def __init__(self, name):
        super().__init__(name)
        self._val = True

    def __call__(self, val):
        raise RuntimeError("A flag does not take values")

    def get(self, *args):
        if args:
            raise ValueError("A flag cannot be passed a default value, it is always True")


class Options:

    def __init__(self):
        self._opts = {}

    def add(self, opt: ValueOp):
        self._opts[opt.name] = opt

    def pop(self, opt: ValueOp, *default):
        if not isinstance(opt, Op):
            raise TypeError("Unsupported option type '{}'".format(type(opt)))
        if len(default) > 1:
            raise ValueError("Can only pass at most one default")

        name = opt.name

        try:
            found = self._opts.pop(name)
        except KeyError:
            if isinstance(opt, Flag):
                return False
            if default:
                return default[0]
            if opt.has_default():
                return opt.default

            raise

        try:
            return found.get(*default)
        except ValueError:
            raise KeyError("Option '{}' does not have a value".format(name))


def separate_opts(*args) -> [Options, list]:
    """Separate out the options from the other arguments"""
    opts = Options()
    rest = []
    for arg in args:
        if isinstance(arg, Op):
            opts.add(arg)
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
        return opts.pop(opts.index(opt)).get(args[0])
    except ValueError:
        if args:
            return args[0]

        raise
