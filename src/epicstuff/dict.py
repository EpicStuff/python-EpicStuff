
from collections import UserDict
from collections.abc import Hashable, Iterator, Mapping
from typing import Any


class Dict(UserDict):  # pyright: ignore[reportRedeclaration]
	'''Basically a dictionary but you can access the keys as attributes (with a dot instead of brackets))

	you can also "bind" it to another `MutableMapping` object
	this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap'''

	def __init__(self, target: Mapping | None = None) -> None:  # pylint: disable=super-init-not-called
		super().__setattr__('data', target if target is not None else {})

	def _wrap(self, val: Any) -> Any:
		if isinstance(val, Mapping):
			return self.__class__(val)
		return val

	# make it so that you can access the keys as attributes
	def __getitem__(self, key: Any) -> Any:
		val = self.data[key]
		return self._wrap(val) if isinstance(val, Mapping) and not isinstance(val, Dict) else val
	def __getattr__(self, key: Hashable) -> Any:
		try:
			return self.__getitem__(key)
		except KeyError as e:
			raise AttributeError(key) from e
	def __setattr__(self, key: str, value: Any) -> None:
		if key == 'data':
			super().__setattr__(key, value)
		else:
			self.data[key] = value
	def __repr__(self) -> str: return f'{self.__class__.__name__}({super().__repr__()})'
	def __reversed__(self) -> Iterator: return reversed(self.data)


OldDict = Dict

class Dict(dict):  # pylint: disable=function-redefined
	'''The class gives access to the dictionary through the attribute name.

	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box
	_convert = None: Convert only the provided mapping to Dict
	_convert = True: Recursively convert all nested mappings to Dicts
	_convert = False: Do not convert mapping to Dict'''

	_protected_keys = {'_convert', '_create', '_do_convert', '_protected_keys'}  # noqa: RUF012

	def __new__(cls, _map: Mapping | None = None, _convert: bool | None = None, **kwargs) -> 'Dict':
		'''"Redirects" to old dict if convert is False

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
		self._convert = _convert or False
		self._create = _create
		if _map is not None:
			self.update(_map)
		self.update(kwargs)
	def __getattr__(self, key: Hashable) -> Any:
		'''Method returns the value of the named attribute of an object.

		:param key: Hashable
		:return: Any'''
		if key not in self and '_create' in self and self._create:
			self[key] = Dict()
		try:
			return self[key]
		except KeyError as e:
			raise AttributeError(key) from e
	def __setattr__(self, key: str, val: Any) -> None:
		'''Method sets the value of given attribute of an object.

		:param key: str
		:param val: Any
		:return: None'''
		if key in self._protected_keys:
			super().__setattr__(key, val)
		elif self._convert:  # convert is true
			self[key] = self._do_convert(val)
		else:  # convert is None
			self[key] = val
	# def __delattr__(self, key: Hashable) -> None:
	# 	# i think, not tested
	# 	try:
	# 		del self[key]
	# 	except KeyError as e:
	# 		raise AttributeError(key) from e
	def __getitem__(self, key: Any) -> Any:
		val = super().__getitem__(key)
		return self._do_convert(val) if self._convert else val
	def __setitem__(self, key: Any, val: Any) -> None:
		return super().__setitem__(key, self._do_convert(val) if self._convert else val)
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({super().__repr__()}, _convert={self._convert})'
	def update(self, _map: Mapping | None = None, **kwargs) -> None:
		for k, v in dict(_map or {}, **kwargs).items():
			self[k] = v

	def _do_convert(self, val: Any) -> Any:
		'''Converts (nested) dicts in dicts or lists to Dicts

		:param val: Any
		:return: Any'''
		if isinstance(val, Dict):
			return val
		if isinstance(val, Mapping):
			return Dict(val, _convert=self._convert)
		if isinstance(val, (list, tuple, set, frozenset)):
			return type(val)(map(self._do_convert, val))
		return val
