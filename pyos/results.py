from typing import Callable


class BaseResults:

    def __or__(self, other: Callable):
        if not isinstance(other, Callable):
            raise ValueError("'{}' is not callable".format(other))

        return other(self)
