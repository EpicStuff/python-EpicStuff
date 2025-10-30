'''misc stuff'''
from collections.abc import Callable
from functools import partial as wrap
from pathlib import Path
from typing import Any

from .dict import Dict

open = wrap(Path.open, encoding='utf8')  # noqa: A001  # pylint: disable=redefined-builtin

def rmap(obj: Any, key_func: Callable | None = None, val_func: Callable | None = None, _list: type[list] = list, _dict: type[dict] = Dict) -> Any:
	# if object is a list, call rmap on each item
	if isinstance(obj, list):
		out = _list([rmap(item, key_func, val_func) for item in obj])
	# if object is a dict, call rmap on each value, and key_func on each key
	elif isinstance(obj, dict):
		out = _dict()
		for key, value in obj.items():
			out[key_func(key) if key_func else key] = rmap(value, key_func, val_func)
	# if object is neither, call val_func on it
	else:
		out = val_func(obj) if val_func else obj
	return out
