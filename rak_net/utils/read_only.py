from __future__ import annotations

__all__ = 'ReadOnlyMeta', 'ReadOnly'


def __is_dunder__(name: str) -> bool:
    """
    Function to check if item is a dunder item (starting and ending with double underscores)

    :param name: Name of the item
    :return: Boolean depicting if object is dunder or not
    """
    return (len(name) > 5) and (name[:2] == name[-2:] == '__') and name[2] != "_" and name[-3] != '_'


def __is_sunder__(name: str) -> bool:
    """
    Function to check if item is a sunder item (starting and ending with single underscores)

    :param name: Name of the item
    :return: Boolean depicting if object is sunder or not
    """
    return (len(name) > 3) and (name[:1] == name[-1:] == '_') and name[1] != "_" and name[-2] != '_'


def __is_descriptor__(obj: object) -> bool:
    """
    Function to check if item is a descriptor (has ``__get__``, ``__set__`` or ``__delete__`` methods)

    :param obj: Object to check
    :return: Boolean depicting if object is a descriptor or not
    """
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class ReadOnlyMeta(type):
    """
    Metaclass for a Read-Only Enum
    """
    def __new__(mcs, name: str, bases: tuple[type], namespace: dict, ignore: bool = None):
        ignore = ignore or []
        members = {k: namespace[k] for k in namespace.keys() if
                   not (__is_sunder__(k) or __is_dunder__(k) or k in ignore or __is_descriptor__(namespace[k]))}
        cls = type.__new__(mcs, name, bases, namespace)
        super().__setattr__(cls, '__members__', members)
        return cls

    def __repr__(self) -> str:
        return f"<Read-Only: {self.__name__}>"

    def __contains__(self, name) -> bool:
        return name in self.__members__.values()

    def __getattr__(self, name):
        if name in self.__members__: return self.__members__[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        raise AttributeError("Can not set attributes.")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Can not delete attributes.")

    def __getitem__(self, name: str):
        return self.__members__[name]

    def __setitem__(self, name, value):
        raise KeyError("Can not edit this key.")

    def __delitem__(self, name):
        raise KeyError("Can not delete this key.")

    def __dir__(self):
        return [*self.__members__.keys()]

    def __iter__(self):
        return (key for key in self.__members__.keys())

    def __reversed__(self):
        return (key for key in reversed(self.__members__.keys()))

    def __len__(self) -> int:
        return len(self.__members__)


class ReadOnly(metaclass=ReadOnlyMeta):
    """
    Class for a Read-Only Enum
    """
    pass
