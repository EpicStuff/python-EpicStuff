import warnings
from abc import ABC
from collections import UserDict
from collections.abc import Callable, Generator, Hashable, Iterable, Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from typing import Any, ClassVar, Literal, Self, overload, TypeVar

from rich.pretty import pretty_repr

try:
	from box import Box as _Box  # pyright: ignore[reportMissingImports]
except ImportError:
	box_installed = False
else:
	box_installed = True

from .permissify import permissify as perm

K = TypeVar('K')
V = TypeVar('V')
def _jdict(target: Mapping | None = None, _convert: bool | None = None, _: Literal[False] = False) -> 'JDict':
	return JDict(target, _convert=_convert)
def _boxdict(_map: Mapping | None = None, _convert: bool | None = None, _create: bool = False) -> 'BoxDict':
	return BoxDict(_map, _convert=_convert, _create=_create)
@contextmanager
def no_create(self: 'Dict') -> Generator:
	if self._create is not False:
		_create = self._create
		self._create = False
		yield
		self._create = _create

class _Mixin:
	# for typing
	_convert: bool | None = False
	_create: bool | Callable = False

	_protected_attrs: ClassVar[set[str]] = {'_protected_attrs'}
	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs) -> None:
		super().__init_subclass__(**kwargs)
		# deal with protected_attrs
		if protected_attrs:
			cls._protected_attrs = cls._protected_attrs | protected_attrs
	def __reduce__(self) -> tuple[type[Self] | Callable, tuple[dict, bool | None, bool]]:
		'''Support pickling of Dict with its conversion and creation flags.'''
		if self.__class__ is JDict:
			return (_jdict, (dict(self), self._convert, False))  # pyright: ignore[reportArgumentType, reportCallIssue]
		if self.__class__ is BoxDict:
			return (_boxdict, (dict(self), self._convert, bool(self._create)))  # pyright: ignore[reportArgumentType, reportCallIssue]
		return (self.__class__, (dict(self), getattr(self, '_convert', None), bool(getattr(self, '_create', False))))  # pyright: ignore[reportArgumentType, reportCallIssue]
	def __repr__(self, max_length: int | None = -1, max_string: int | None = -1, max_depth: int | None = -1, max_total: int | None = 512, default_convert_value: bool | None = None) -> str:
		'Truncates long reprs. Set max to None to disable. -1 to use default.'
		from .trace import get_trace_kwargs  # noqa: PLC0415

		_trace_kwargs = get_trace_kwargs()

		_max_length = _trace_kwargs.get('locals_max_length', 16)
		_max_string = _trace_kwargs.get('locals_max_string', 160)
		_max_depth = _trace_kwargs.get('locals_max_depth', 4)

		base = pretty_repr(  # @IgnoreException
			self._t if isinstance(self, JDict) else dict(self), max_width=10_000,  # pyright: ignore[reportArgumentType, reportCallIssue]
			max_length=_max_length if (max_length is not None and max_length < 0) else max_length,
			max_string=_max_string if (max_string is not None and max_string < 0) else max_string,
			max_depth=_max_depth if (max_depth is not None and max_depth < 0) else max_depth,
		)
		if max_total and len(base) > max_total:
			base = base[:max_total - 3] + '...'
		return f'{self.__class__.__name__}({base}' + (f', _convert={c})' if (c := getattr(self, '_convert', None)) is not default_convert_value else ')')  # pylint: disable=E0601

# the dict is to make cls.__bases__ =  work
class Dict(_Mixin, ABC, dict[K, V]):  # pyright: ignore[reportRedeclaration]
	'''Dispatcher class that redirects to either JDict or BoxDict based on _convert parameter along with @overloads for typing. And redirects subclassing to BoxDict.'''

	_protected_attrs: ClassVar[set[str]] = {'_protected_attrs'}

	@overload
	def __new__(cls, _map: Mapping | list | None = None, *_: Any, _convert: Literal[True] | None = True, _create: bool = False, **kwargs) -> 'BoxDict': ...  # pylint: disable=W1113
	@overload
	def __new__(cls, target: Mapping, *,  _convert: Literal[False] = False) -> 'JDict': ...
	def __new__(cls, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = False, _create: bool = False,  **kwargs) -> 'Dict':  # pyright: ignore[reportInconsistentOverload] pylint: disable=W1113
		'''"Redirects" to boxdict if convert, else to jdict.'''
		# if _convert is explicitly specified as False, use jdict
		if cls is Dict:
			if _convert is False:
				return JDict(_map, **kwargs)  # pyright: ignore[reportArgumentType, reportReturnType]
			return BoxDict(_map, _convert=_convert, _create=_create, **kwargs)  # pyright: ignore[reportReturnType]
		# else use boxdict
		return super().__new__(cls)  # pyright: ignore[reportReturnType]

	@overload
	def _do_convert(self, val: Any, *args: Any, **kwargs: Any) -> Any: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]
	@overload
	def __getattr__(self, key: str) -> Any: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]

	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs) -> None:
		# if they wrote class Something(Dict) rather than class Something(BoxDict)
		if Dict in cls.__bases__:
			# replace Dict with BoxDict in the bases tuple
			cls._warn()
			cls.__bases__ = tuple((BoxDict if base is Dict else base) for base in cls.__bases__)
			cls._protected_attrs = BoxDict._protected_attrs.copy()
		# deal with protected_attrs when subclassed
		if protected_attrs:
			cls._protected_attrs = cls._protected_attrs | protected_attrs
	@classmethod
	def _warn(cls) -> None:
		warnings.warn(
			f'{cls.__name__} subclasses Dict directly, using BoxDict instead.\n\tThis warning can be also disabled by adding `def _warn(): pass` to the subclass.',
			UserWarning,
			stacklevel=2,
		)


_Dict = Dict

# JDict
class Dict[K, V](_Mixin, protected_attrs={'_convert', '_wrap', '_t'}):  # pyright: ignore[reportIncompatibleMethodOverride, reportRedeclaration] # pylint: disable=function-redefined  # noqa: PLW1641
	'''Basically a dictionary but you can access the keys as attributes (with a dot instead of brackets)).

	you can also "bind" it to another `MutableMapping` object
	this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap'''

	def __init__(self, target: Mapping | None = None, *_: Any,  _convert: bool | None = None, _create: bool = False, **kwargs) -> None:  # pylint: disable=W1113
		'''Initialize a Dict pointing to an existing mapping.

		:param target: Optional mapping to wrap; defaults to a new dict.
		:param _convert: Conversion behavior for nested mappings (None/True/False).
		'''
		if target is None:
			target = {}
		self._t = target
		if kwargs:
			self.update(kwargs)

		self._convert = _convert

	# make it so that you can access the keys as attributes
	def __getitem__(self, key: Any) -> Any:
		'''Return item by key, converting to JDict unless already _convert=False.'''
		if key in self._t:
			return self._wrap(self._t[key])
		if hasattr(self.__class__, "__missing__"):
			return self.__class__.__missing__(self, key)  # pyright: ignore[reportAttributeAccessIssue]
		raise KeyError(key)
	def __getattr__(self, key: str) -> Any:
		'''Attribute style access for keys.'''
		if key in self._t:
			return self.__getitem__(key)
		if key in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			raise AttributeError(key)  # @IgnoreException
		return self._t.__getattribute__(key)
	def __setattr__(self, key: str, value: Any) -> None:
		'''Attribute style setting for keys, unless protected.'''
		if key in self._protected_attrs:
			super().__setattr__(key, value)
		else:
			self._t[key] = value
	def __delattr__(self, key: Hashable) -> None:
		'''Delete attribute by removing corresponding key; raises AttributeError if missing.'''
		try:
			del self[key]
		except KeyError:
			raise AttributeError(key) from None

	# filling-out the abstract methods + methods in dicts but not in MutableMapping
	def __len__(self) -> int: return self._t.__len__()
	def __setitem__(self, key: Hashable, item: Any) -> None: self._t.__setitem__(key, item)
	def __delitem__(self, key: Hashable) -> None: self._t.__delitem__(key)
	def __iter__(self) -> Iterator[Any]: return self._t.__iter__()
	def __contains__(self, key: Hashable) -> bool: return self._t.__contains__(key)
	def get(self, key: Hashable, default: Any = None) -> Any: return self._t.get(key, default)
	def __or__(self, other: Mapping) -> Self | Any: return self._wrap(self._t.__or__(other))  # pyright: ignore[reportCallIssue]
	def __ror__(self, other: Mapping) -> Self | Any: return self._wrap(self._t.__ror__(other))  # pyright: ignore[reportCallIssue]
	def __ior__(self, other: Mapping) -> Self:
		if isinstance(other, type(self)):
			self._t |= other._t
		elif isinstance(other, UserDict):
			self._t |= other.data
		else:
			self._t |= other
		return self
	def __copy__(self) -> Mapping:
		if hasattr(self._t, "__copy__"):
			return self._wrap(self._t.__copy__())  # pyright: ignore[reportAttributeAccessIssue]
		import copy  # noqa: PLC0415
		return self._wrap(copy.copy(self._t))
	def __deepcopy__(self, memo: dict[int, Any] | None = None, _nil: Any = []) -> Mapping:  # noqa: B006
		if hasattr(self._t, "__deepcopy__"):
			return self._wrap(self._t.__deepcopy__(memo, _nil))  # pyright: ignore[reportAttributeAccessIssue]
		import copy  # noqa: PLC0415
		return self._wrap(copy.deepcopy(self._t, memo, _nil))
	def copy(self) -> Mapping:
		if hasattr(self._t, "copy"):
			return self._wrap(self._t.copy())  # pyright: ignore[reportAttributeAccessIssue]
		return self.__copy__()
	@classmethod
	def fromkeys(cls, iterable: Iterable, value: Any = None) -> Self:
		self = cls()
		for key in iterable:
			self[key] = value
		return self
	def __reversed__(self) -> Iterator: return self._t.__reversed__()  # pyright: ignore[reportAttributeAccessIssue]
	def keys(self, _list: bool = True) -> Any: keys = self._t.keys(); return list(keys) if _list else keys  # pyright: ignore[reportAttributeAccessIssue]
	def items(self, _list: bool = True) -> Any: items = self._t.items(); return [(item[0], self._wrap(item[1])) for item in items] if _list else items  # pyright: ignore[reportAttributeAccessIssue]
	def values(self, _list: bool = True) -> list | Any: values = self._t.values(); return [self._wrap(value) for value in values] if _list else values  # pyright: ignore[reportAttributeAccessIssue]
	def __eq__(self, other: Mapping) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
		out = NotImplemented
		# use self._t's eq if it has it, in case ._t has special eq
		if hasattr(self._t, '__eq__'):
			out = self._t.__eq__(other)
		# if not, try other's eq in case other has special eq
		elif hasattr(other, '__eq__'):
			out = other.__eq__(self)
		# if neither worked, do mapping's comparison if other is a mapping
		if out is NotImplemented and isinstance(other, Mapping):
			return dict(self.items()) == dict(other.items())
		# else, return not implemented
		return out

	# stuff
	def update(self, _map: Mapping | Iterable[tuple[Any, Any]] = (), /, **kwargs: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
		'''To avoid _wrap being called when _convert is None, causing updating values to be converted.'''
		if isinstance(_map, type(self)):
			self._t.update(_map._t, **kwargs)  # pyright: ignore[reportAttributeAccessIssue] # noqa: SLF001
		else:
			self._t.update(_map, **kwargs)  # pyright: ignore[reportAttributeAccessIssue]
	def _wrap(self, val: Any) -> Any:
		if self._convert is not False and isinstance(val, Mapping) and not isinstance(val, Dict):
			return self.__class__(val)
		return val


_Dict.register(Dict)
MutableMapping.register(Dict)  # pyright: ignore[reportAttributeAccessIssue]
JDict = Dict

# BoxDict, TODO: turn _convert, _create into @property that sets the value of children
class Dict(_Mixin, dict[K, V], protected_attrs={'_convert', '_converter', '_create', '_do_convert'}):  # pylint: disable=function-redefined
	'''The class gives access to the dictionary through the attribute name.

	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box

	`_convert = None`: Convert only the mapping to Dict on getattr/getitem
	`_convert = True`: Recursively convert all nested mappings to Dicts on setattr/setitem/getattr/getitem
	`_convert = False`: Do not convert mapping to Dict

	`_converter: Callable | None`: use callable to convert value when value is a mapping if not None

	`_create: bool = False`: Should auto create nested Dicts on access?'''

	_convert: bool | None = None
	def __init__(self, _map: Mapping | list | None = None, *_: Any, _convert: bool | None = True, _create: bool = False, _converter: Callable | None = None, **kwargs) -> None:  # pylint: disable=W1113
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
		# for rich's pretty repr (for boxdict with _create in jdict)
		if self._convert is not False and key in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			raise AttributeError(key)  #@IgnoreException

		try:
			return self[key]
		except KeyError:
			raise AttributeError(key) from None
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
		# if _convert is False or is allready type(self), return as is
		if self._convert is False or isinstance(val, type(self)):
			return val
		# if _convert is True, convert to be safe
		if self._convert is True:
			self[key] = val
			return super().__getitem__(key)
		# if _convert is None, convert using jdict so changes are reflected to parent
		if isinstance(val, list):
			print('Warning: _convert is None and returned value is list, assignment wont work')
		coverter = self._converter
		self._converter = JDict
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
	def values(self, _list: Literal[False]) -> Any: ...
	def values(self, _list: bool = True) -> list | Any:  # pyright: ignore[reportIncompatibleMethodOverride]
		'''Return values as a list by default.'''
		items = super().values()
		return list(items) if _list else items
	def hasattr(self, key: str) -> bool:
		'''Check if attribute exists as key, ignoring _create.'''
		if key in self.__dict__:
			return True
		with no_create(self):
			return hasattr(self, key)
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

	def __repr__(self) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
		return super().__repr__(default_convert_value=True)


_Dict.register(Dict)
BoxDict = Dict
Dict = _Dict  # pyright: ignore[reportAssignmentType]

if box_installed:
	class Box(_Box):  # pyright: ignore[reportRedeclaration]
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
