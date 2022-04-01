# -*- coding: utf-8 -*-
from typing import Callable, TextIO


class BaseResults:

    def __or__(self, other: Callable):
        if not isinstance(other, Callable):  # pylint: disable=isinstance-second-argument-not-valid-type
            raise ValueError(f"'{other}' is not callable")

        return other(self)

    def __stream_out__(self, stream: TextIO):
        """Stream the string representation of this object to the output stream"""
        stream.write(self.__str__())
