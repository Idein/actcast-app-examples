from typing import Tuple, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


# Type alias for shorthand.
ResultTuple = Union[Tuple[T, None], Tuple[None, E]]
