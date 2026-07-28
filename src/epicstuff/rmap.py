from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence, Set
from functools import partial as wrap
from typing import Any, Self


class with_arg:
	def __new__(cls, func: Callable | None, *args: str) -> Self | None:
		if func is None:
			return None
		if isinstance(func, cls):
			return func
		return super().__new__(cls)
	def __init__(self, func: Callable | None, *args: str) -> None:
		if self is func:
			assert args == ()
			return

		assert func is not None  # for typing
		self.func: Callable = func
		self.args: tuple[str, ...] = args
	def __call__(self, item: Any, **context: Any) -> Any:
		if 'key' not in context:
			context['key'] = context['path'][-1]

		extras = list(self.args)
		for num, extra in enumerate(extras):
			assert extra in context, f'{extra} is not a valid extra'
			extras[num] = context[extra]
		return self.func(item, *extras)

def rmap(
	obj: Mapping | Sequence | Set, val_func: Callable | None = None, key_func: Callable | None = None,
	_list: Callable | None = None, _dict: Callable | None = None, _sequence: type | tuple[type, ...] = (list, tuple, set, frozenset), **kwargs: Any,
) -> Any:
	'''Recursively inplace run functions on key, values, and items of a dict or list.

	Args:
		obj: The dict/list to recursively call funcs on
		val_func: Called on each non container value
		key_func: Called on each mapping key
		_dict: Func to call on key_func return, if provided
		_list: Func to call on val_func return, if provided
		_sequence: what counts as a list, eg. yes sets but not str

	By default mutable containers are updated in place and an immutable one are rebuilt as its own type,
	pass _dict/_list to convert instead.

	Use `with_arg(callback, ['key' | 'path' | 'value'])` to pass extra values to a callback.

	'''
	self: wrap | None = kwargs.get('self')
	if self is None:
		val_func = with_arg(val_func); key_func = with_arg(key_func); _list = with_arg(_list); _dict = with_arg(_dict)
		self = wrap(rmap, val_func=val_func, key_func=key_func, _list=_list, _dict=_dict, _sequence=_sequence)
		self.keywords['self'] = self
	path: tuple = kwargs.get('path', ())

	# if object is a list, call self on each item
	if isinstance(obj, _sequence):
		new = [self(item, path=(*path, index)) for index, item in enumerate(obj)]
		if _list is not None:
			return _list(new, path=path)
		# if mutable, make the change in place; else rebuild as its own type
		if isinstance(obj, MutableSequence):
			obj[:] = new
			return obj
		return type(obj)(new)
	# if object is a dict, call self on each value, and key_func on each key
	if isinstance(obj, Mapping):
		if key_func is not None:
			new = {key_func(key, value=value, path=(*path, key)): self(value, path=(*path, key)) for key, value in obj.items()}
		else:
			new = {key: self(value, path=(*path, key)) for key, value in obj.items()}

		if _dict is not None:
			return _dict(new, path=path)
		# if mutable, make change in place
		if isinstance(obj, MutableMapping):
			obj.clear()
			obj.update(new)
			return obj
		return type(obj)(new)
	# if object is neither, call val_func on it
	return val_func(obj, path=path) if val_func is not None else obj
