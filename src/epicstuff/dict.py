import warnings
from collections import UserDict
from collections.abc import Callable, Generator, Hashable, Iterable, Iterator, Mapping, ValuesView
from contextlib import contextmanager
from functools import partial as wrap
from typing import Any, ClassVar, Literal, Self, overload

try:
	from box import Box as _Box
except ImportError:
	box_installed = False
else:
	box_installed = True

from .permissify import permissify as perm
from .s import String as s


def _jdict(target: Mapping | None = None, _convert: bool | None = None, _: Literal[False] = False) -> 'JDict':
	return JDict(target, _convert=_convert)
def _boxdict(_map: Mapping | None = None, _convert: bool | None = None, _create: bool = False) -> 'BoxDict':
	return BoxDict(_map, _convert=_convert, _create=_create)


class Dict(dict):  # pyright: ignore[reportRedeclaration]
	'''Dispatcher class that redirects to either JDict or BoxDict based on _convert parameter along with @overloads for typing.'''

	_protected_attrs: ClassVar[set[str]] = set()

	@overload
	def __new__(cls, target: Mapping, *,  _convert: Literal[False]) -> 'JDict': ...
	@overload
	def __new__(cls, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = None, _create: bool = False, **kwargs) -> 'BoxDict': ...  # pylint: disable=W1113
	def __new__(cls, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = None, _create: bool = False,  **kwargs) -> 'Dict':  # pyright: ignore[reportInconsistentOverload] pylint: disable=W1113
		'''"Redirects" to boxdict if convert, else to jdict.'''
		# if _convert is explicitly specified as False, use old dict
		if cls is Dict:
			if _convert is False:
				return JDict(_map, **kwargs)  # pyright: ignore[reportReturnType]
			return BoxDict(_map, _convert=_convert, _create=_create, **kwargs)  # pyright: ignore[reportReturnType]
		return super().__new__(cls)  # pyright: ignore[reportReturnType]

	@overload
	def _do_convert(self, val: Any, *args: Any, **kwargs: Any) -> Any: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]
	@overload
	def __getattr__(self, key: str) -> Any: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]

	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs) -> None:
		# deal with protected_attrs
		if protected_attrs:
			cls._protected_attrs |= protected_attrs
		# if its the 2 Dicts below, skip
		if cls.__module__ == __name__:
			return
		# if they wrote class Something(Dict) rather than class Something(BoxDict)
		if Dict in cls.__bases__:
			# replace Dict with BoxDict in the bases tuple
			cls._warn()
			cls.__bases__ = tuple((BoxDict if base is Dict else base) for base in cls.__bases__)
	@classmethod
	def _warn(cls) -> None:
		warnings.warn(
			f'{cls.__name__} subclasses Dict directly, using BoxDict instead.\n\tThis warning can be also disabled by adding `def _warn(): pass` to the subclass.',
			UserWarning,
			stacklevel=2,
		)
class _Mixin:
	def __reduce__(self) -> tuple[type[Self] | Callable, tuple[dict, bool | None, bool]]:
		'''Support pickling of Dict with its conversion and creation flags.'''
		if self.__class__ is JDict:
			return (_jdict, (dict(self), self._convert, False))
		if self.__class__ is BoxDict:
			return (_boxdict, (dict(self), self._convert, bool(self._create)))
		return (self.__class__, (dict(self), getattr(self, '_convert', None), getattr(self, '_create', False)))
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({super().__repr__()}' + (f', _convert={c})' if (c := getattr(self, '_convert', None)) is not None else ')')


_Dict = Dict

class Dict(_Mixin, UserDict, _Dict, protected_attrs={'_convert', '_wrap', '_protected_attrs', 'data'}):  # pyright: ignore[reportIncompatibleMethodOverride, reportRedeclaration] # pylint: disable=function-redefined
	'''Basically a dictionary but you can access the keys as attributes (with a dot instead of brackets)).

	you can also "bind" it to another `MutableMapping` object
	this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap'''

	def __init__(self, target: Mapping | None = None, _convert: bool | None = None, _create: bool = False) -> None:  # pylint: disable=super-init-not-called
		'''Initialize a Dict pointing to an existing mapping.

		:param target: Optional mapping to wrap; defaults to a new dict.
		:param _convert: Conversion behavior for nested mappings (None/True/False).
		'''
		if '_convert' not in self.__dict__:  # double init guard
			super().__setattr__('data', target if target is not None else {})
			self._convert = _convert

	def _wrap(self, val: Any) -> Any:
		if self._convert is not False and isinstance(val, Mapping):
			return self.__class__(val)
		return val

	# make it so that you can access the keys as attributes
	def __getitem__(self, key: Any) -> Any:
		'''Return item by key, converting to JDict unless already _convert=False.'''
		return self._wrap(val) if isinstance(val := self.data[key], Mapping) and not isinstance(val, Dict) else val
	def __getattr__(self, key: str) -> Any:
		'''Attribute style access for keys.'''
		if key in self.data:
			return self.__getitem__(key)
		return self.data.__getattribute__(key)
	def __setattr__(self, key: str, value: Any) -> None:
		'''Attribute style setting for keys, unless protected.'''
		if key in self._protected_attrs:
			super().__setattr__(key, value)
		else:
			self.data[key] = value
	def __reversed__(self) -> Iterator:
		'''Return an iterator over items in reverse insertion order.'''
		# return self._wrap(reversed(self.data))
		return reversed(self.data)

	def update(self, _map: Mapping | Iterable[tuple[Any, Any]], /, **kwargs: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
		'''To avoid _wrap being called when _convert is None, causing updating values to be converted.'''
		if isinstance(_map, JDict):
			self.data.update(_map.data, **kwargs)
		else:
			super().update(_map, **kwargs)


	# def __or__(self: Self, value: Any) -> UnionType | Self:
	# 	return super().__or__(value)
	# def __ror__(self: Self, value: Any) -> UnionType | Self:
	# 	return super().__ror__(value)
JDict = Dict

class Dict(_Mixin, _Dict, protected_attrs={'_convert', '_converter', '_create', '_do_convert', '_protected_attrs'}):  # pylint: disable=function-redefined
	'''The class gives access to the dictionary through the attribute name.

	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box

	`_convert = None`: Convert only the mapping to Dict on getattr/getitem
	`_convert = True`: Recursively convert all nested mappings to Dicts on setattr/setitem/getattr/getitem
	`_convert = False`: Do not convert mapping to Dict

	`_converter: Callable | None`: use callable to convert value when value is a mapping if not None

	`_create: bool = False`: Should auto create nested Dicts on access?'''

	_convert: bool | None = None
	# @overload
	# def __new__(cls, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = None, _create: bool = False, **kwargs) -> Self: ...  # pyright: ignore[reportNoOverloadImplementation, reportInconsistentOverload] pylint: disable=W1113
	def __init__(self, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = None, _create: bool = False, _converter: Callable | None = None, **kwargs) -> None:  # pylint: disable=W1113
		'''Initialize Dict with optional mapping and conversion flags.

		:param _map: Mapping to populate from.
		:param _convert: Conversion behavior for nested mappings (None/True/False).
		:param _create: If True, auto-create nested Dicts on attribute access.
		:param kwargs: Additional key-value pairs to add.
		'''
		if '_create' not in self.__dict__:  # double init guard
			if isinstance(_map, Dict):
				if hasattr(_map, '_convert'):
					_convert = _map._convert  # noqa: SLF001
				if hasattr(_map, '_create') and _map._create is not False:  # noqa: SLF001
					_create = True

			self._convert = _convert
			self._converter = _converter
			if _create is False:
				self._create: Callable | Literal[False] = _create
			super().__init__()
			if _map is not None:
				self.update(_map)
			self.update(kwargs)

			if self._create and self._convert is False:
				print('Warning: _create=True with _convert=None will cause ')
	def __getattr__(self, key: str) -> Any:
		'''Return the value of the named attribute of an object.

		:param key: Hashable
		:return: Any'''
		return self[key]
	def __setattr__(self, key: str, val: Any) -> None:
		'''Set the value of given attribute of an object.

		:param key: str
		:param val: Any
		:return: None'''
		if key in self._protected_attrs:
			super().__setattr__(key, val)
		else:  # convert is None
			self[key] = val
	def __delattr__(self, key: Hashable) -> None:
		'''Delete attribute by removing corresponding key; raises AttributeError if missing.'''
		try:
			del self[key]
		except KeyError:
			raise AttributeError(key) from None
	def __getitem__(self, key: Any) -> Any:
		'''Get value by key, converting return if _convert is not False.'''
		# if key not in self and self._create
		if key not in self and self._create:
			self[key] = val = self._create()
			return val
		# else
		val = super().__getitem__(key)
		if self._convert is False or isinstance(val, type(self)):
			return val
		# kinda tmp
		if isinstance(val, list):
			print('Warning: _convert is not False and returned value is list, expect weird behavior')
		coverter = self._converter
		self._converter = wrap(_tmp_dict, parent=self, key=key)
		val = perm(self._do_convert)(val, key)
		self._converter = coverter
		return val
	def __setitem__(self, key: Any, val: Any) -> None:
		'''Set key to value, applying conversion when `_convert` is True.'''
		super().__setitem__(key, perm(self._do_convert)(val, key) if self._convert is True else val)

	def _do_convert(self, val: Any, *args: Any, **kwargs: Any) -> Any:
		'''Convert (nested) dicts in dicts or lists to Dicts.

		:param val: Any
		:param key: str, optional, doesn't get used but can be useful for subclass overrides
		:return: Any'''
		if isinstance(val, type(self)):
			return val
		if isinstance(val, Mapping):
			return perm(self._converter if self._converter else self.__class__)(val, *args, _convert=self._convert, _create=self._create, _converter=self._converter, **kwargs)
		if isinstance(val, (list, tuple, set, frozenset)):
			return val.__class__([perm(self._do_convert)(item, *args, **kwargs) for item in val])  # passing the args and kwargs for potential subclass overrides
		return val
	def _create(self) -> Self:  # pyright: ignore[reportRedeclaration] # pylint: disable=E0202
		return perm(self.__class__)(_convert=self._convert, _create=True, _converter=self._converter)

	def update(self, __m: Any = None, /, **kwargs: Any) -> None:
		'''`__m` is not actually `Any`.'''
		for k, v in dict(__m or {}, **kwargs).items():
			self[k] = v
	@overload
	def values(self) -> list[Any]: ...
	@overload
	def values(self, _list: Literal[True] = True) -> list[Any]: ...
	@overload
	def values(self, _list: Literal[False]) -> ValuesView[Any]: ...
	def values(self, _list: bool = True) -> list | ValuesView:  # pyright: ignore[reportIncompatibleMethodOverride]
		'''Return values as a list by default.'''
		items = super().values()
		return list(items) if _list else items
	def hasattr(self, key: str) -> bool:
		'''Check if attribute exists as key, ignoring _create.'''
		if key in self.__dict__:
			return True
		if self._create is not False:
			_create = self._create
			self._create = False
			_hasattr = hasattr(self, key)
			self._create = _create
			return _hasattr
		return hasattr(self, key)
	def getattr(self, key: str, default: Any = None) -> Any:
		'''Get attribute by key, returning default if missing, ignoring _create.'''
		if hasattr(self, key):
			return getattr(self, key)
		return default

	def __ror__(self: Self, value: Any) -> Self | dict:
		return Dict(value := super().__ror__(value)) if self._convert is not False else value
	def __or__(self: Self, value: Any) -> Self | dict:
		return Dict(value := super().__or__(value)) if self._convert is not False else value

class _tmp_dict(Dict, protected_attrs={'_parent', '_key'}):
	'tmp dict so when getitem then setitem is called, changes are reflected to parent dict and not just the newly created dict by getitem. '
	def __init__(self, *args, parent: Dict, key: str, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self._parent = parent
		self._key = key
	def __setitem__(self, key: Any, val: Any) -> None:
		super().__setitem__(key, val)
		# if being run by __init__, skip the rest
		if '_parent' not in self.__dict__:
			return
		# update parent
		if isinstance(self._parent[self._key], list):
			print('Warning: setitem with lists is not supported with _convert=None, set it to either true or false')
		convert = self._parent._convert
		self._parent._convert = False
		self._parent[self._key][key] = self._do_convert(val, key) if self._parent._convert else val
		self._parent._convert = convert


BoxDict = Dict

Dict = _Dict  # pyright: ignore[reportAssignmentType]

if box_installed:
	class Box(_Box):
		'''A "wrapper" around `box.Box`.'''

		_extra_configs: ClassVar[set[str]] = set()  # these values will be auto added to self._box_config if passed to __init__ or __setattr__. _box_config will be passed to converted objects
		_protected_attrs: ClassVar[set[str]] = _extra_configs | set()  # these values will be set as attributes instead of being passed to __setitem__
		def __init_subclass__(cls, extra_configs: set[str] | None = None, protected_attrs: set[str] | None = None) -> None:
			if extra_configs:
				cls._extra_configs |= extra_configs
				cls._protected_attrs |= extra_configs
			if protected_attrs:
				cls._protected_attrs |= protected_attrs

		def __init__(self, _map: Any = None, **kwargs: Any) -> None:
			with self._update_config(kwargs):
				super().__init__(() if _map is None else _map, **kwargs)
		def __setattr__(self, key: str, value: Any) -> None:
			if key in self._protected_attrs:
				if key in self._extra_configs:
					if self._box_config['__created'] is False:
						print('Warning: Setting `_extra_config` args before calling `super().__init__` will have them removed from `_config`.')
					self._box_config[key] = value
				object.__setattr__(self, key, value)
			else:
				super().__setattr__(key, value)
		def __repr__(self) -> str:
			return f'{self.__class__.__name__}({dict.__repr__(self)})'
		def __str__(self) -> str:
			return self.__repr__()
		@contextmanager
		def _update_config(self, kwargs: dict[str, Any]) -> Generator:
			keys = {}
			for key in self._extra_configs:
				if key in kwargs:
					keys[key] = kwargs.pop(key)
			yield
			for key, val in keys.items():
				self._box_config[key] = val
else:
	def Box(*args: Any, **kwargs: Any) -> None:
		'''Dummy Box class when `box` package is not installed.'''
		raise ImportError('BoxDict requires the `box` package to be installed.')
