from collections.abc import Callable, Mapping, Sequence, Set
from typing import Any


class with_arg:
	def __init__(self, func: Callable, *args: str) -> None: ...
def rmap(
	obj: Mapping | Sequence | Set, val_func: Callable | None = None, key_func: Callable | None = None,
	_list: Callable | None = None, _dict: Callable | None = None, _sequence: type | tuple[type, ...] = ...,
) -> Any: ...
