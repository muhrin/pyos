# -*- coding: utf-8 -*-
from typing import Callable


class BaseResults:

    def __or__(self, other: Callable):
        if not isinstance(other, Callable):  # pylint: disable=isinstance-second-argument-not-valid-type
            raise ValueError("'{}' is not callable".format(other))

        return other(self)
