__all__ = 'Option', 'Options', 'separate_opts', 'option'


class Option:
    """An option that can be accepted by a command"""

    def __init__(self, name, call_params=()):
        self._name = name
        self._params_stack = call_params

    def __str__(self):
        parts = ["-", self.name]
        for params in self._params_stack:
            args = params[0]
            kwargs = params[1]

            params = list(str(arg) for arg in args)
            params.extend(tuple("{}={}".format(key, value) for key, value in kwargs.items()))
            parts.extend(('(', ",".join(params), ')'))

        return "".join(parts)

    def __call__(self, *args, **kwargs):
        if len(self._params_stack) == 2:
            raise RuntimeError("Option already has filled parameters")

        params = list(self._params_stack)
        params.append((args, kwargs))
        return Option(self.name, tuple(params))

    def __neg__(self):
        """Allow so a user can optional use a dash when passing this as an argument"""
        return self

    @property
    def called(self) -> bool:
        return bool(self._params_stack)

    @property
    def params_stack(self) -> tuple:
        return self._params_stack

    @property
    def name(self):
        return self._name

    def new(self):
        """Get a new option of this type"""
        return Option(self.name)


class OptionSpec:

    def __init__(self, option: Option, is_flag=True):
        self.option = option
        self.is_flag = is_flag


class Options:
    """Container storing options value, using this with separate_opts makes writing tools much
     easier"""

    def __init__(self):
        self._opts = {}  # typing.MutableMapping[str, Option]

    def __str__(self):
        return " ".join((str(val) for val in self._opts.values()))

    def __contains__(self, item):
        if isinstance(item, Option):
            return item.name in self._opts
        if isinstance(item, str):
            return item in self._opts

        return False

    def add(self, name, value):
        self._opts[name] = value

    def pop(self, opt: Option, *default):
        if not isinstance(opt, Option):
            raise TypeError("Unsupported option type '{}'".format(opt))
        if len(default) > 1:
            raise ValueError("Can only pass at most one default")

        name = opt.name
        return self._opts.pop(name, default[0] if default else None)

    def update(self, other):
        for name, opt in other._opts.items():
            if name not in self._opts:
                self._opts[name] = opt
            else:
                raise ValueError("Option '{}' alreday specified!".format(name))


def separate_opts(*args) -> [Options, list]:
    """Separate out the options from the other arguments"""
    opts = Options()
    rest = []
    for arg in args:
        if isinstance(arg, Option):
            params_stack = arg.params_stack
            value = True
            if params_stack and params_stack[0] and params_stack[0][0]:
                value = params_stack[0][0][0]

            opts.add(arg.name, value)
        elif isinstance(arg, Options):
            opts.update(arg)
        else:
            rest.append(arg)
    return opts, rest


class Command:
    """Class representing a command"""

    def __init__(self, func: callable):
        self.func = func
        self.accepts = {}

    @property
    def name(self) -> str:
        return self.func.__name__

    def add_opt(self, spec: OptionSpec):
        """Add an option that this command accepts"""
        self.accepts[spec.option.name] = spec

    def __call__(self, *args, **kwargs):
        """Execute this command directly"""
        options, rest = separate_opts(*args)
        return self.func(options, *rest, **kwargs)

    def __sub__(self, other: Option):
        """Start an execution of this command by supplying options"""
        builder = CommandBuilder(self)
        return builder - other


class CommandBuilder:
    """Used when a command is being built by options being passed to it"""

    def __init__(self, cmd: Command):
        self.command = cmd
        self.options = Options()

    def execute(self, *args, **kwargs):
        return self.command(self.options, *args, **kwargs)

    def __sub__(self, other: Option):
        unsupported = ValueError("Command does not accept option: {}".format(other))

        if isinstance(other, Option):
            # We have an option instance so it could be an option with a value or the
            # arguments are actually meant for the command
            try:
                spec = self.command.accepts[other.name]
            except KeyError:
                raise unsupported
            else:
                params_stack = list(other.params_stack)

                if spec.is_flag:
                    self.options.add(other.name, True)
                    if params_stack:
                        # Assume the parameters are for the command, but make sure only one
                        assert len(params_stack) == 1, \
                            "Flag '{}' does not take any parameters".format(other.name)
                else:
                    option_params = params_stack.pop(0)  # tuple of (args, kwargs)
                    assert not option_params[1], "Can't supply kwargs to an option"
                    value = True
                    if option_params[0]:
                        value = option_params[0][0]
                    self.options.add(other.name, value)

                # Now the arguments of the option have been dealt with, see if we should execute
                if params_stack:
                    args, kwargs = params_stack.pop()
                    return self.execute(*args, **kwargs)

                # Carry on
                return self

        raise unsupported

    def __str__(self) -> str:
        return " ".join((self.command.name, str(self.options)))


def option(opt: Option):
    """Decorator for defining an option taken by a command function"""
    spec = OptionSpec(opt, is_flag=False)

    def attach(func):
        if isinstance(func, Command):
            cmd = func
        else:
            cmd = Command(func)

        cmd.add_opt(spec)
        return cmd

    return attach


def flag(opt: Option):
    """Decorator for defining an option taken by a command function"""
    spec = OptionSpec(opt, is_flag=True)

    def attach(func):
        if isinstance(func, Command):
            cmd = func
        else:
            cmd = Command(func)

        cmd.add_opt(spec)
        return cmd

    return attach
