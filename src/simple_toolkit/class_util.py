# /usr/bin/python
# -*- coding: UTF-8 -*-

__all__ = ["AttrSet"]


class AttrSet(set):
    """A set that can be initialized with its own class attributes.

    :Example:
    >>> class MySet(AttrSet):
            ATTR1 = 1
            ATTR2 = 2
    >>> myset = MySet()
    >>> print(myset) -> {1, 2}
    >>> print(myset.ATTR1) -> 1
    """

    def __init__(self):
        values = [
            getattr(self, i)
            for i in [i for i in vars(self.__class__) if not i.startswith("__")]
        ]
        super().__init__(values)

    def __str__(self) -> str:
        return str(set(self))
