
from collections import UserDict
from collections.abc import Hashable, Iterator, Mapping
from typing import Any


class _ReprMixin:
	_convert: bool | None = None
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({super().__repr__()}' + (f', _convert={self._convert})' if self._convert is not None else ')')


class Dict(_ReprMixin, UserDict):  # pyright: ignore[reportRedeclaration]
	'''Basically a dictionary but you can access the keys as attributes (with a dot instead of brackets)).

	you can also "bind" it to another `MutableMapping` object
	this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap'''

	_protected_keys = {'_convert', '_wrap', '_protected_keys', 'data'}  # noqa: RUF012

	def __init__(self, target: Mapping | None = None, _convert: bool | None = None) -> None:  # pylint: disable=super-init-not-called
		super().__setattr__('data', target if target is not None else {})
		self._convert = _convert

	def _wrap(self, val: Any) -> Any:
		if self._convert is not False and isinstance(val, Mapping):
			return self.__class__(val)
		return val

	# make it so that you can access the keys as attributes
	def __getitem__(self, key: Any) -> Any:
		val = self.data[key]
		return self._wrap(val) if isinstance(val, Mapping) and not isinstance(val, Dict) else val
	def __getattr__(self, key: Hashable) -> Any:
		try:
			return self.__getitem__(key)
		except KeyError:
			raise AttributeError(key) from None
	def __setattr__(self, key: str, value: Any) -> None:
		if key in self._protected_keys:
			super().__setattr__(key, value)
		else:
			self.data[key] = value
	def __reversed__(self) -> Iterator: return reversed(self.data)


OldDict = Dict

class Dict(_ReprMixin, dict):  # pylint: disable=function-redefined
	'''The class gives access to the dictionary through the attribute name.

	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box
	_convert = None: Convert only the provided mapping to Dict
	_convert = True: Recursively convert all nested mappings to Dicts
	_convert = False: Do not convert mapping to Dict'''

	_protected_keys = {'_convert', '_create', '_do_convert', '_protected_keys'}  # noqa: RUF012

	def __new__(cls, _map: Mapping | None = None, _convert: bool | None = None, _: bool = False,  **kwargs) -> 'Dict':
		'''"Redirects" to old dict if convert is False.

		:param _map: Optional[Mapping]
		:param _convert: Optional[bool]
		:param _create: bool
		:param kwargs: Any
		:return: Dict'''
		# if _convert is explicitly specified as False, use old dict
		if _convert is False:
			return OldDict(_map, **kwargs)  # pyright: ignore[reportReturnType]
		return super().__new__(cls)

	def __init__(self, _map: Mapping | None = None, _convert: bool | None = None, _create: bool = False, **kwargs) -> None:
		super().__init__()
		self._convert = _convert
		self._create = _create
		if _map is not None:
			self.update(_map)
		self.update(kwargs)
	def __getattr__(self, key: Hashable) -> Any:
		'''Return the value of the named attribute of an object.

		:param key: Hashable
		:return: Any'''
		if key not in self and '_create' in self and self._create:
			self[key] = Dict(_convert=self._convert, _create=self._create)
		try:
			return self[key]
		except KeyError:
			raise AttributeError(key) from None
	def __setattr__(self, key: str, val: Any) -> None:
		'''Set the value of given attribute of an object.

		:param key: str
		:param val: Any
		:return: None'''
		if key in self._protected_keys:
			super().__setattr__(key, val)
		elif self._convert:  # convert is true
			self[key] = self._do_convert(val, key)
		else:  # convert is None
			self[key] = val
	def __delattr__(self, key: Hashable) -> None:
		try:
			del self[key]
		except KeyError:
			raise AttributeError(key) from None
	def __getitem__(self, key: Any) -> Any:
		val = super().__getitem__(key)
		if self._convert is False:
			return val
		return self._do_convert(val, key)
	def __setitem__(self, key: Any, val: Any) -> None:
		return super().__setitem__(key, self._do_convert(val, key) if self._convert else val)
	def __reduce__(self) -> tuple[type['Dict'], tuple[dict, bool, bool]]:
		return (self.__class__, (dict(self), getattr(self, '_convert', False), getattr(self, '_create', False)))
	def update(self, __m: Any = None, /, **kwargs: Any) -> None:
		'''`__m` is not actually `Any`.'''
		for k, v in dict(__m or {}, **kwargs).items():
			self[k] = v

	def _do_convert(self, val: Any, *_: str) -> Any:
		'''Convert (nested) dicts in dicts or lists to Dicts.

		:param val: Any
		:return: Any'''
		if isinstance(val, Dict):
			return val
		if isinstance(val, Mapping):
			return Dict(val, _convert=self._convert)
		if isinstance(val, (list, tuple, set, frozenset)):
			return type(val)(map(self._do_convert, val))
		return val
