from __future__ import annotations

import abc, warnings
from collections import UserDict
from collections.abc import Callable, Generator, Hashable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import _GeneratorContextManager, contextmanager, suppress
from enum import Enum, auto
from typing import Any, ClassVar, Final, Literal, Self, overload, TYPE_CHECKING

from rich.pretty import pretty_repr

from .permissify import permissify as perm
from .stuff import rmap

if TYPE_CHECKING:
	from _collections_abc import dict_items, dict_keys, dict_values


_DEPRECATED_WARNED: set[str] = set()
def _warn_deprecated(cls_name: str) -> None:
	'Warn once per class that JDict/BoxDict (and the dispatching `Dict`) will be replaced by `NewDict`.'
	if cls_name in _DEPRECATED_WARNED:
		return
	_DEPRECATED_WARNED.add(cls_name)
	warnings.warn(
		f'{cls_name} is deprecated. `Dict` will point to `NewDict` in future update. Use `OldDict`, `JDict`, or `BoxDict` explicitly to keep current behavior.',
		FutureWarning,
		stacklevel=3,
	)
def _jdict(target: Mapping | None = None, _convert: bool | None = None, _: Literal[False] = False) -> JDict:
	'To make pickle work.'
	return JDict(target, _convert=_convert)
def _boxdict(_map: Mapping | None = None, _convert: bool | None = None, _create: bool = False) -> BoxDict:
	'To make pickle work.'
	return BoxDict(_map, _convert=_convert, _create=_create)
def _newdict(source: Mapping, settings: _Settings) -> NewDict:
	return NewDict(source, **settings)
@contextmanager
def no_create(self: _Mixin | NewDict) -> Generator:
	'Temporarily disable _create.'
	if isinstance(self, NewDict):
		if self._s.create is not False:
			create = self._s.create
			self._s.create = False
			yield
			self._s.create = create
		else:
			yield
		return
	if self._create is not False:
		_create = self._create
		self._create = False
		yield
		self._create = _create
	else:
		yield

class _Mixin:
	'Shared methods.'

	# for typing
	_convert: bool | None = False
	_create: Literal[False] | Callable = False

	_protected_attrs: ClassVar[set[str]] = {'_protected_attrs'}
	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs) -> None:  # pyright: ignore[reportMissingParameterType]
		'Handle protected_attrs for subclasses.'
		super().__init_subclass__(**kwargs)
		# deal with protected_attrs
		if protected_attrs:
			cls._protected_attrs = cls._protected_attrs | protected_attrs
	def __reduce__(self) -> tuple[type[Self] | Callable, tuple[dict, bool | None, bool]]:
		'Support pickling of Dict with its conversion and creation flags.'
		if self.__class__ is JDict:
			return (_jdict, (dict(self), self._convert, False))  # pyright: ignore[reportArgumentType, reportCallIssue]
		if self.__class__ is BoxDict:
			return (_boxdict, (dict(self), self._convert, bool(self._create)))  # pyright: ignore[reportArgumentType, reportCallIssue]
		return (self.__class__, (dict(self), getattr(self, '_convert', None), bool(getattr(self, '_create', False))))  # pyright: ignore[reportArgumentType, reportCallIssue]
	def __repr__(self, max_length: int | None = -1, max_string: int | None = -1, max_depth: int | None = -1, max_total: int | None = 512, default_convert_value: bool | None = None) -> str:
		'Truncate long reprs. Set max to None to disable. -1 to use default.'
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

# the `dict` is to make cls.__bases__ =  work
class Dict[K, V](_Mixin, abc.ABC, dict):  # pyright: ignore[reportRedeclaration]
	'Dispatcher class that redirects to either JDict or BoxDict based on _convert parameter along with @overloads for typing. And redirects subclassing to BoxDict.'

	_protected_attrs: ClassVar[set[str]] = {'_protected_attrs'}

	def __new__(cls, _map: Mapping | Sequence | None = None, *_: Any, _convert: bool | None = False, _create: bool | Callable = False,  **kwargs) -> 'Self | JDict | BoxDict':  # pylint: disable=W1113   # pyright: ignore
		'"Redirects" to boxdict if convert, else to jdict.'
		# if ?
		if cls is Dict:  # pyright: ignore[reportUnnecessaryComparison]
			# if _convert and _create is False, use jdict
			if _convert is False and _create is False:
				return JDict(_map, **kwargs)  # pyright: ignore[reportArgumentType]
			# else either or both _convert or _create is changed, use boxdict
			return BoxDict(_map, _convert=_convert, _create=_create, **kwargs)
		# else ?
		return super().__new__(cls)

	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs) -> None:  # pyright: ignore
		'Redirect subclassing to BoxDict + Handle protected_attrs for subclasses.'
		# if they wrote class Something(Dict) rather than class Something(BoxDict)
		if Dict in cls.__bases__:
			# replace Dict with BoxDict in the bases tuple
			cls._warn()
			cls.__bases__ = tuple((BoxDict if base is Dict else base) for base in cls.__bases__)  # pyright: ignore
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

	# for pylint typing
	def __getattr__(self, key: str) -> Any: return self[key]
	def __setattr__(self, key: str, value: Any) -> None: self[key] = value
	def __delattr__(self, key: Hashable) -> None: del self[key]


_Dict = Dict

# JDict
class Dict[K, V](_Mixin, protected_attrs={'_convert', '_wrap', '_t'}):  # pyright: ignore[reportRedeclaration]  # noqa: PLW1641
	'''Basically a dictionary but you can access the keys as attributes (with a dot instead of brackets)).

	you can also "bind" it to another `MutableMapping` object
	this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap
	'''

	def __init__(self, target: Mapping | None = None, *_: Any,  _convert: bool | None = None, _create: bool | Callable = False, **kwargs) -> None:  # pylint: disable=keyword-arg-before-vararg  # pyright: ignore
		'''Initialize a Dict pointing to an existing mapping.

		:param target: Optional mapping to wrap; defaults to a new dict.
		:param _convert: Conversion behavior for nested mappings (None/True/False).
		'''
		_warn_deprecated('JDict')
		if target is None:
			target = {}
		self._t = target  # pyright: ignore
		if kwargs:
			self.update(kwargs)

		self._convert = _convert  # pyright: ignore

	# make it so that you can access the keys as attributes
	def __getitem__(self, key: Any) -> Any:
		'Return item by key, converting to JDict unless already _convert=False.'
		if key in self._t:
			return self._wrap(self._t[key])
		if hasattr(self.__class__, '__missing__'):
			return self.__class__.__missing__(self, key)  # pyright: ignore[reportAttributeAccessIssue]
		raise KeyError(key)
	def __getattr__(self, key: str) -> Any:
		'Attribute style access for keys.'
		if key in self._t:
			return self.__getitem__(key)
		if key in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			raise AttributeError(key)  # @IgnoreException
		return self._t.__getattribute__(key)
	def __setattr__(self, key: str, value: Any) -> None:
		'Attribute style setting for keys, unless protected.'
		if key in self._protected_attrs:
			super().__setattr__(key, value)
		else:
			self._t[key] = value  # pyright: ignore[reportIndexIssue]
	def __delattr__(self, key: Hashable) -> None:
		'Delete attribute by removing corresponding key; raises AttributeError if missing.'
		if key in self._protected_attrs:
			super().__delattr__(key)  # pyright: ignore
			return
		try:
			del self[key]
		except KeyError:
			raise AttributeError(key) from None

	# filling-out the abstract methods + methods in dicts but not in MutableMapping
	def __len__(self) -> int: return self._t.__len__()
	def __setitem__(self, key: Hashable, item: Any) -> None: self._t.__setitem__(key, item)  # pyright: ignore[reportAttributeAccessIssue]
	def __delitem__(self, key: Hashable) -> None: self._t.__delitem__(key)  # pyright: ignore[reportAttributeAccessIssue]
	def __iter__(self) -> Iterator[Any]: return self._t.__iter__()
	def __contains__(self, key: Hashable) -> bool: return self._t.__contains__(key)
	def get(self, key: Hashable, default: Any = None) -> Any: return self._t.get(key, default)
	def __or__(self, other: Mapping) -> Self | Any: return self._wrap(self._t.__or__(other))  # pyright: ignore[reportArgumentType, reportAttributeAccessIssue]
	def __ror__(self, other: Mapping) -> Self | Any: return self._wrap(self._t.__ror__(other))  # pyright: ignore[reportArgumentType, reportAttributeAccessIssue]
	def __ior__(self, other: Mapping) -> Self:
		if isinstance(other, type(self)):
			self._t |= other._t  # pyright: ignore[reportOperatorIssue]
		elif isinstance(other, UserDict):
			self._t |= other.data  # pyright: ignore[reportOperatorIssue]
		else:
			self._t |= other  # pyright: ignore[reportOperatorIssue]
		return self
	def __copy__(self) -> Mapping:
		if hasattr(self._t, "__copy__"):
			return self._wrap(self._t.__copy__())  # pyright: ignore[reportAttributeAccessIssue]
		import copy  # noqa: PLC0415
		return self._wrap(copy.copy(self._t))
	def __deepcopy__(self, memo: dict[int, Any] | None = None, _nil: Any = []) -> Mapping:  # noqa: B006  # pyright: ignore
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
	def keys(self, _list: bool = True) -> Any: keys = self._t.keys(); return list(keys) if _list else keys
	def items(self, _list: bool = True) -> Any: items = self._t.items(); return [(item[0], self._wrap(item[1])) for item in items] if _list else items
	def values(self, _list: bool = True) -> list | Any: values = self._t.values(); return [self._wrap(value) for value in values] if _list else values
	def __eq__(self, other: Mapping) -> bool:
		out = NotImplemented
		# use self._t's eq if it has it, in case ._t has special eq
		if hasattr(self._t, '__eq__'):
			out = self._t.__eq__(other)
		# if not, try other's eq in case other has special eq
		elif hasattr(other, '__eq__'):
			out = other.__eq__(self)
		# if neither worked, do mapping's comparison if other is a mapping
		if out is NotImplemented and isinstance(other, Mapping):  # pyright: ignore
			return dict(self.items()) == dict(other.items())
		# else, return not implemented
		return out

	# stuff
	def update(self, _map: Mapping | Iterable[tuple[Any, Any]] = (), /, **kwargs: Any) -> None:
		'To avoid _wrap being called when _convert is None, causing updating values to be converted.'
		if isinstance(_map, type(self)):
			self._t.update(_map._t, **kwargs)  # pyright: ignore[reportAttributeAccessIssue]
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
class Dict[K, V](_Mixin, dict, protected_attrs={'_convert', '_converter', '_create', '_do_convert'}):  # pylint: disable=function-redefined
	'''The class gives access to the dictionary through the attribute name.

	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box

	`_convert = None`: Convert only the mapping to Dict on getattr/getitem
	`_convert = True`: Recursively convert all nested mappings to Dicts on setattr/setitem/getattr/getitem
	`_convert = False`: Do not convert mapping to Dict

	`_converter: Callable | None`: use callable to convert value when value is a mapping if not None

	`_create: bool = False`: Should auto create nested Dicts on access?
	'''

	_convert: bool | None = None
	def __init__(self, _map: Mapping | Sequence | None = None, *_: Any, _convert: bool | None = True, _create: bool | Callable = False, _converter: Callable | None = None, **kwargs) -> None:  # pylint: disable=W1113  # pyright: ignore
		'''Initialize Dict with optional mapping and conversion flags.

		:param _map: Mapping to populate from.
		:param _convert: Conversion behaviour for nested mappings (None/True/False).
		:param _create: If True, auto-create nested Dicts on attribute access.
		:param kwargs: Additional key-value pairs to add.
		'''
		_warn_deprecated('BoxDict')
		# if map is Dict, inherit its settings
		if isinstance(_map, Dict):
			if hasattr(_map, '_convert'):
				_convert = _map._convert
			if hasattr(_map, '_create') and _map._create is not False:
				_create = True

		self._convert = _convert
		self._converter = _converter  # pyright: ignore
		if _create is False:
			self._create = _create
		else:
			self._create = self._create
		super().__init__()
		if _map is not None:
			self.update(_map)
		self.update(kwargs)

		if self._create and self._convert is False:
			print('Warning: _create=True with _convert=None will maybe cause issues.')
	def __getattr__(self, key: str) -> Any:
		'''Return the value of the named attribute of an object.

		:param key: Hashable
		:return: Any
		'''
		# for rich's pretty repr (for boxdict with _create in jdict)
		if self._convert is not False and key in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			raise AttributeError(key)  # @IgnoreException

		try:
			return self[key]
		except KeyError:
			raise AttributeError(key) from None
	def __setattr__(self, key: str, val: Any) -> None:
		'Set the value of given attribute of an object.'
		if key in self._protected_attrs:
			super().__setattr__(key, val)
		else:
			self[key] = val
	def __delattr__(self, key: Hashable) -> None:
		'Delete attribute by removing corresponding key; raises AttributeError if missing.'
		try:
			del self[key]
		except KeyError:
			raise AttributeError(key) from None
	def __getitem__(self, key: Any) -> Any:
		'Get value by key, converting return if _convert is not False.'
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
		'Set key to value, applying conversion when `_convert` is True.'
		super().__setitem__(key, perm(self._do_convert)(val, key) if self._convert is True else val)

	def _do_convert(self, val: Any, *args: Any, **kwargs: Any) -> Any:
		'''Convert (nested) dicts in dicts or lists to Dicts.

		:param val: Any
		:param key: str, optional, doesn't get used but can be useful for subclass overrides
		:return: Any
		'''
		self._create: Callable | Literal[False]

		if isinstance(val, type(self)):
			return val
		if isinstance(val, Mapping):
			return perm(self._converter if self._converter else self.__class__)(val, *args, _convert=self._convert, _create=self._create, _converter=self._converter, **kwargs)
		if isinstance(val, (list, tuple, set, frozenset)):
			return val.__class__([perm(self._do_convert)(item, *args, **kwargs) for item in val])  # passing the args and kwargs for potential subclass overrides
		return val
	def _create(self) -> Self:  # pyright: ignore[reportRedeclaration] # pylint: disable=E0202
		'Create new Dict with same settings, set to False to disable auto creation.'
		return perm(self.__class__)(_convert=self._convert, _create=True, _converter=self._converter)

	def update(self, __m: Any = None, /, **kwargs: Any) -> None:
		'`__m` is not actually `Any`.'
		for k, v in dict(__m or {}, **kwargs).items():
			self[k] = v
	def keys(self, _list: bool = True) -> list[Hashable] | dict_keys:
		if _list:
			return list(super().keys())
		return super().keys()
	def values(self, _list: bool = True) -> list | dict_values:
		'Return values as a list by default.'
		items = super().values()
		return list(items) if _list else items
	def items(self, _list: bool = True) -> list[tuple[Hashable, Any]] | Any:
		if _list:
			return list(super().items())
		return super().items()
	def hasattr(self, key: str) -> bool:
		'''Check if attribute exists as key, ignoring _create.'''
		if key in self.__dict__:
			return True
		with no_create(self):
			return hasattr(self, key)
		return hasattr(self, key)  # pyright: ignore
	def getattr(self, key: str, default: Any = None) -> Any:
		'''Get attribute by key, returning default if missing, ignoring _create.'''
		if hasattr(self, key):
			return getattr(self, key)
		return default

	def __ror__(self: Self, value: Any) -> Self:
		'Called by other | self, self overwrites other (including _convert, _...).'  # noqa: D401
		value = super().__ror__(value)
		if self._convert is not False:
			return self.__class__(value, _convert=self._convert, _create=self._create, _converter=self._converter)
		return value
	def __or__(self: Self, other: Any) -> Self | Any:
		'Called by self | other, other overwrites self.'  # noqa: D401
		if isinstance(other, UserDict):
			other = super().__or__(other.data)
		elif isinstance(other, JDict):
			other = super().__or__(other._t)  # pyright: ignore[reportArgumentType]
		# run other's ror instead if other is box dict
		elif isinstance(other, BoxDict):
			return other.__ror__(self)
		elif isinstance(other, dict):
			other = super().__or__(other)
		else:
			return NotImplemented
		# if its userdict, jdict, or dict, return self.__class__ if _convert is not False
		return self.__class__(other) if self._convert is not False else other

	def __repr__(self) -> str:
		return super().__repr__(default_convert_value=True)


_Dict.register(Dict)
BoxDict = Dict
Dict = _Dict  # pyright: ignore[reportAssignmentType]

# New Dict
class _Unset(Enum):	UNSET = auto()
_unset: Final = _Unset.UNSET
type Op[O] = O | _Unset
def Copy[K, V](obj: Mapping[K, V], copy: Any = None) -> Mapping[K, V]:  # noqa: N802, uppercase since `copy` gets used as arg
	'''Custom copy function, because it seems for some reason, python can't do copy itself.'''  # noqa: D401
	from copy import copy as copy_fn  # noqa: PLC0415

	# if obj has copy that works, use it (doesn't default to dict.copy)
	if callable(getattr(obj, 'copy', None)):
		copy = obj.copy()  # pyright: ignore[reportAttributeAccessIssue]
	# else, resort to copy.copy
	if copy != obj or type(copy) is not type(obj) or copy is obj:
		copy = copy_fn(obj)
	# if that still doesn't work, give obj.__class__(obj) a try
	if copy != obj:
		copy = type(obj)(obj)  # pyright: ignore[reportCallIssue]
		# copy = type(obj)(copy)  # maybe consider doing obj.__class__(copy) instead
	if copy != obj:
		raise TypeError(f'Could not copy {obj}')
	return copy
# not inside NewDict._demote for performance reasons (not recreating each run)
@contextmanager
def with_demote(self: NewDict, strict: bool) -> Generator:
	if self._cls is None:
		if strict:
			raise TypeError('Cannot demote a plain NewDict (dict source)')
		yield
	else:
		class_ = self.__class__
		self.__class__ = self._source_cls
		try:
			yield
		finally:
			self.__class__ = class_
class NewDict[K, V](dict[K, V]):
	'''Allow access of items as attributes.

	`_copy = True`: Shallow copy source, changes to either will(/should) not be reflected on the other
	`_copy = False`: Explicit not copy, will raise error if source is not supported
	`_copy = None`: Default option. Does not copy unless is `dict`

	`_convert = True`: Recursively convert on set (not get)
	`_convert = None`: Convert only on get (Note conversion does happen on get), Note: dicts inside lists, etc. wont be converted, even on get
	`_convert = False`: Do not convert

	`_create = True`: Yes create not existing items on access
	`_create = False`: No, don't create

	`_converter: Callable | None`: Optional Callable to use when converting mappings
	`_creater: Callable | None` Optional Callable to use when creating on access
	'''

	# when you do class newclass(NewDict), newclass will be called a subclass
	# when you do NewDict(SomeClass), it creates dotSomeClass, dotSomeClass will be called a child class
	# and SomeClass is the source

	_protected_attrs: ClassVar[set[str]] = {'_protected_attrs', '_s', '_do_convert', '__class__', '_childclass_cache', '_cls', '_source_cls'}
	_okay_private_keys: set[str] = set()  # keys that start and end with _ that is should be created when _create is not False
	
	# for init
	_childclass_cache: dict[type, type] = {}
	_cls: None | type = None  # this is used to keep track of if is child class, points to the original not source class
	@classmethod
	def _get_subclass(cls, source: type) -> type:
		'Build (and cache) a subclass of `source` that is mixed with Dict.'
		# check if class for source already exists
		new_cls = cls._childclass_cache.get(source)
		if new_cls is not None:
			return new_cls
		# create new class for source (as dotSource(NewDict, source)) and cache it
		new_cls = type(f'dot{source.__name__}', (cls, source), {})
		new_cls._cls = cls
		cls._childclass_cache[source] = new_cls
		return new_cls
	def __new__(
		cls, source: Mapping[K, V] | Sequence[tuple[K, V]] | None = None, _copy: bool | None = None,
		_convert: Op[bool | None] = _unset, _create: Op[bool] = _unset,
		_converter: Op[Callable] = _unset, _creater: Op[Callable] = _unset,
		**_kwargs: Any,
	) -> Self:
		# make wrong source type error clearer
		assert source is None or isinstance(source, (Mapping, list, tuple)), 'wrong type, has to be mapping, list/tuple, or none'

		# `dict` cannot have its class changed so return Dict (none or list creates dict)
		if type(source) is dict or source is None or isinstance(source, (list, tuple)):
			if _copy is False:
				raise TypeError( f'_copy=False not supported. {type(source).__name__} cannot be wrapped without copying.')
			obj = super().__new__(cls)
			# if source is None or list/tuple, means init has not been called, record that
			if type(source) is not dict:
				obj._source_cls = None  # pyright: ignore[reportAttributeAccessIssue]
			return obj
		# else, there is a non dict source that needs to be dealt with

		# copy if _copy is true (not none or false)
		if _copy: source = Copy(source)
		# "initiate"/convert source
		if not isinstance(source, cls):
			source.__class__ = cls._get_subclass(type(source))
		
		return source  # pyright: ignore[reportReturnType]
	def __init__(
		self, source: Mapping[K, V] | Sequence[tuple[K, V]] | None = None, _copy: bool | None = None,
		_convert: Op[bool | None] = _unset, _create: Op[bool] = _unset,
		_converter: Op[Callable] = _unset, _creater: Op[Callable] = _unset,
		**kwargs: Any,
	) -> None:
		# if source has not been init-ed, init (this can happen if child class gets created directly with no source)
		source_not_inited = self.hasattr('_source_cls', True)
		if source_not_inited:
			super().__init__(**kwargs) if source is None else super().__init__(source, **kwargs)  # super init might not accept a None source  # pylint: disable=expression-not-assigned

		# update properties
		self._s: _Settings[K, V] = _Settings(self, _convert, _create, _converter, _creater, self.getattr('_s', {}, True))

		# update items, for "dict" source
		if type(source) is dict or isinstance(source, list):
			self.update(source)
		# skip this if init was already run with kwargs
		if not source_not_inited:
			self.update(kwargs)
		# set remaining properties
		if self._cls is None:
			self._source_cls = dict
		else:
			self._source_cls: type = type(self).__bases__[1]  # this also indicates that init is done

	# core functionality
	def __getattr__(self, key: str) -> Any:
		'Redirect to getitem unless special.'
		is_key_special = key in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '_fields') or (key not in self._okay_private_keys and key.startswith('_') and key.endswith('_'))
		# to prevent recursion
		if key in self._protected_attrs:
			return self.__getattribute__(key)
		# if key exists or we're creating and it's not a special key, get item
		if key in self or (self._s.create and not is_key_special):
			return self.__getitem__(key)  # pyright: ignore[reportArgumentType]  # attribute access is str-keyed, K may differ
		# else, fetch it without special Dict stuff, super().__getattr__ causes issues with some sources
		with self._demote():
			return self.__getattribute__(key)
	def __setattr__(self, key: str, val: Any) -> None:
		'Redirect to setitem unless protected or already exists.'
		if key in self._protected_attrs or self.hasattr(key, True):
			super().__setattr__(key, val)
		else:
			self[key] = val  # pyright: ignore[reportArgumentType]  # attribute access is str-keyed, K may differ
	def __delattr__(self, key: Hashable) -> None:
		'Redirect to __delitem__.'
		if key in self._protected_attrs:
			super().__delattr__(key)  # pyright: ignore[reportArgumentType]
		else:
			try:
				del self[key]  # pyright: ignore[reportArgumentType]  # attribute access is str-keyed, K may differ
			except KeyError:
				raise AttributeError(key) from None
	def __missing__(self, key: Hashable) -> NewDict:
		'Deal with when self._s.create is True.'
		if self._s.create:
			self[key] = val = self._s.creater(key)  # pyright: ignore[reportArgumentType]  # __missing__ key is dynamic vs K, _creater returns Self
			return val
		raise KeyError(key)
	def __getitem__(self, key: K) -> V:
		'Get value by key, converting return if _convert is not False.'
		val = super().__getitem__(key)
		# if _convert is False or True (true assumes already converted so get is faster) or is already type(self), return as is
		if self._s.convert is not None or isinstance(val, type(self)):
			return val  # pyright: ignore[reportReturnType]  # converted value may be wrapped as Self, still the logical V
		# if _convert is None and is not a Dict subclass, convert and save
		if isinstance(val, Mapping) and not isinstance(val, (self._cls or type(self))):
			converted = self._s.converter(val, key)
			# (save) convert on get so changes to returned obj are reflected
			self[key] = converted
			return converted
		# else, is not mapping or is already a Dict, return as is
		return val
	def __setitem__(self, key: K, val: V) -> None:
		'Set key to value, applying conversion when `_convert` is True.'
		super().__setitem__(key, self._do_convert(val, key) if self._s.convert is True else val)

	# advanced functionality
	def _promote(self, obj: Any) -> Self:
		'Turn dict into Dict or swap class.'
		if type(obj) is dict:
			return type(self)(obj, **self._s)
		obj.__class__ = type(self)
		obj._source_cls = self._source_cls
		obj._s = _Settings(obj, **self._s)
		return obj
	@overload
	def _demote(self, copy: Literal[False] = False, strict: bool = False) -> _GeneratorContextManager: ...
	@overload
	def _demote(self, copy: Literal[True], strict: bool = False) -> Mapping: ...
	def _demote(self, copy: bool = False, strict: bool = False) -> Mapping | _GeneratorContextManager:
		'If copy, returns original class as copy else, convert back to original class, and does nothing if source is plain dict.'
		if copy:
			if self._cls is None:
				return dict(self)
			with with_demote(self, strict):
				source = Copy(self)
			# get rid of extra Dict attributes
			for attr in {'_s', '_source_cls', '_cls'}:
				with suppress(AttributeError):
					delattr(source, attr)
			return source
		return with_demote(self, strict)

	def _do_convert(self, val: Any, *args: Any, **kwargs: Any) -> Any:  # todo: look into replacing with rmap
		'Recursively convert Mappings to self.'
		if isinstance(val, type(self)):
			return val
		if isinstance(val, Mapping):
			return self._s.converter(val, *args, **kwargs)
		if isinstance(val, (list, tuple)):
			return val.__class__([perm(self._do_convert)(item, *args, **kwargs) for item in val])  # passing the args and kwargs for potential subclass overrides
		return val
	def _converter(self, val: Any, _: Hashable) -> Self:
		'Default method of converting to val to type(self).'
		# gets passed key in case subclass overwrite wants it
		# self._cls then type(self) to avoid dottmp turning into dotdottmp i think
		return (type(self) if self._cls is None else self._cls)(val, **self._s)
	def _creater(self, _: Hashable) -> Self:
		'Default method of creating new type(self).'
		# passing key in case subclass overwrite wants it
		return type(self)(**self._s)
	def __copy__(self) -> Self: return self.copy()
	def copy(self) -> Self:
		if self._cls is None:
			copy = dict(self)
		else:
			with self._demote():
				copy = Copy(self)
		return self._promote(copy)

	# stuff
	## "greedy" return
	def __ror__(self: Self, other: Any) -> Self | Any:
		'Called by `other | self`, self overwrites other, self keeps settings.'  # noqa: D401
		if isinstance(other, UserDict):
			other = other.data
		out = super().__ror__(other)
		if out is NotImplemented:
			return out
		return type(self)(out, **self._s)
	def __or__(self: Self, other: Any) -> Self | Any:
		'Called by `self | other`, other overwrites self, self keeps settings.'  # noqa: D401
		if isinstance(other, UserDict):
			other = other.data
		out = super().__or__(other)
		if out is NotImplemented:
			return out
		return self._promote(out)
	## Overwrite C level methods so convert runs if convert
	def update(self, __m: Mapping | Sequence[tuple[K, V]] | None = None, /, **kwargs: Any) -> None:
		'`__m` is not actually `Any`.'
		if self._s.convert is not True:
			super().update(__m or (), **kwargs)
		else:
			for k, v in dict(__m or {}, **kwargs).items():
				self[k] = v
	@overload
	def get(self, key: K) -> V | None: ...
	@overload
	def get(self, key: K, default: V) -> V: ...
	@overload
	def get[T](self, key: K, default: T) -> V | T: ...
	def get(self, key: K, default: Any = None) -> Any:
		'Never create.'
		return self[key] if key in self else default  # noqa: SIM401
	@overload
	def pop(self, key: K) -> V: ...
	@overload
	def pop[T](self, key: K, default: T) -> V | T: ...
	def pop(self, key: K, default: Any = _unset) -> Any:
		if key not in self:
			if default is _unset:
				raise KeyError(key)
			return default
		val = self[key]
		super().__delitem__(key)
		return val
	def popitem(self) -> tuple[K, V]:
		if not self:
			raise KeyError('popitem(): dictionary is empty')
		key = next(reversed(self.keys(False)))
		return key, self.pop(key)
	def setdefault(self, key: K, default: Any = None) -> Any:
		if key not in self:
			self[key] = default
		return self[key]
	def __ior__(self, other: Any) -> Self:
		'Called by `self |= other`, in place, self keeps settings.'  # noqa: D401
		self.update(other)
		return self
	## add support for subclassing and pickling
	def __init_subclass__(cls, protected_attrs: set[str] | None = None, **kwargs: Any) -> None:
		'''Handle protected_attrs for subclasses and make so subclasses don't share subclass cache.'''
		cls._childclass_cache = {}
		super().__init_subclass__(**kwargs)
		# deal with protected_attrs
		if protected_attrs:
			cls._protected_attrs = cls._protected_attrs | protected_attrs
	def __reduce__(self) -> tuple[Callable, tuple[Mapping, dict[str, SettingValue]]]:
		'For pickle.'
		return (_newdict, (self._demote(True), dict(self._s)))
	## personal preference, prefer return list instead
	@overload
	def keys(self, _list: Literal[True] = True) -> list[K]: ...
	@overload
	def keys(self, _list: Literal[False]) -> dict_keys[K, V]: ...  # pylint: disable=invalid-sequence-index
	def keys(self, _list: bool = True) -> list[K] | dict_keys[K, V]:  # pylint: disable=invalid-sequence-index
		if _list:
			return list(super().keys())
		return super().keys()
	@overload
	def values(self, _list: Literal[True] = True) -> list[V]: ...
	@overload
	def values(self, _list: Literal[False]) -> dict_values[K, V]: ...  # pylint: disable=invalid-sequence-index
	def values(self, _list: bool = True) -> list[V] | dict_values[K, V]:  # pylint: disable=invalid-sequence-index
		'Return values as a list by default.'
		vals = super().values()
		return list(vals) if _list else vals
	@overload
	def items(self, _list: Literal[True] = True) -> list[tuple[K, V]]: ...
	@overload
	def items(self, _list: Literal[False]) -> dict_items[K, V]: ...  # pylint: disable=invalid-sequence-index
	def items(self, _list: bool = True) -> list[tuple[K, V]] | dict_items[K, V]:  # pylint: disable=invalid-sequence-index
		if _list:
			return list(super().items())
		return super().items()
	## make work with _create=True
	def hasattr(self, key: str, simple: bool = False) -> bool:
		'''Check if attribute exists as key, ignoring _create.'''
		if key in self.__dict__:
			return True
		if simple:
			return False
		with no_create(self):
			return hasattr(self, key)
	def getattr(self, key: str, default: Any = None, simple: bool = False) -> Any:
		'''Get attribute by key, returning default if missing, ignoring _create.'''
		if self.hasattr(key, simple):
			return getattr(self, key)
		return default
	## extra helper functions
	def drop(self, *keys: K, copy: bool = False) -> Self:
		if copy:
			self = self.copy()
		for key in keys:
			self.pop(key, None)
		return self

type SettingValue = bool | None | Callable | _Unset
class _Settings[K, V](dict):
	'Simple dict with attribute access that favors keys over attributes.'

	parent: NewDict
	convert: bool | None = None
	create: bool = False
	_keys: frozenset[Literal['_convert', '_create', '_converter', '_creater']] = frozenset(('_convert', '_create', '_converter', '_creater'))
	def __init__(self, parent: NewDict, _convert: Op[bool | None] = _unset, _create: Op[bool] = _unset, _converter: Op[Callable] = _unset, _creater: Op[Callable] = _unset, s: dict = {}) -> None:  # pyright: ignore[reportCallInDefaultInitializer]
		kwargs = {key: val for key, val in locals().items() if val is not _unset and key in self._keys}
		super().__init__(s)
		object.__setattr__(self, 'parent', parent)
		self.update(kwargs)
	def __getattribute__(self, key: str) -> Any:
		'Favour keys over attributes.'
		converted_key = super().__getattribute__('convert_key')(key)
		if super().__contains__(converted_key):
			return super().__getitem__(converted_key)
		return super().__getattribute__(key)
	def __getattr__(self, key: str) -> SettingValue:
		'Simplified NewDict functionality.'
		key = self.convert_key(key)
		# key = super().__getattr__('convert_key')
		try:
			return self[key]
		except KeyError as e:
			raise AttributeError(key) from e
	def __setattr__(self, key: str, value: SettingValue) -> None:
		'Simplified NewDict functionality.'
		key = self.convert_key(key)
		if key not in self._keys:
			raise AttributeError(f'{key} is not a valid setting')
		self[key] = value
	def __setitem__(self, key: str, value: SettingValue) -> None:
		'Key check.'
		if key not in self._keys:
			raise KeyError(f'{key} is not a valid setting')
		return super().__setitem__(key, value)
	def __contains__(self, key: str | Any) -> bool:
		if not isinstance(key, str):
			return False
		return super().__contains__(self.convert_key(key))

	def convert_key(self, key: str) -> str:
		if not key.startswith('_'):
			return '_' + key
		return key

	def converter(self, val: Any, key: Hashable) -> NewDict[K, V]:
		return self.parent._converter(val, key)
	def creater(self, key: Hashable) -> NewDict[K, V]:
		return self.parent._creater(key)

_Dict.register(NewDict)




# todo:
# - make sure that NewDict(userdict) works
# - for newdict, maybe add a _parent so when u do a.b['c'], changes to b can be reflected to a without converting on get
# - concider replacing super().func with with _demote: self.func
# - look into getting rid of _do_convert
# - move typing over to dict.pyi
# - move all the _ settings into _s
