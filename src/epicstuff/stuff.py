import atexit, inspect, io, sys
from collections.abc import Callable, Generator, Mapping, MutableMapping, MutableSequence, Sequence
from contextlib import contextmanager
from functools import partial as wrap
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import IO, Any, BinaryIO, Literal, TextIO, overload


type TextMode = Literal['r', 'w', 'a', 'x', 'rt', 'wt', 'at', 'xt', 'r+', 'w+', 'a+', 'x+', 'rt+', 'wt+', 'at+', 'xt+', 'r+t', 'w+t', 'a+t', 'x+t']
type BinaryMode = Literal['rb', 'wb', 'ab', 'xb', 'rb+', 'wb+', 'ab+', 'xb+', 'r+b', 'w+b', 'a+b', 'x+b']
@overload
def open(path: str | Path, mode: TextMode = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> io.TextIOWrapper: ...  # noqa: A001
@overload
def open(path: str | Path, mode: BinaryMode, encoding: None = None, **kwargs: Any) -> BinaryIO: ...  # noqa: A001
@overload
def open(path: str | Path, mode: str = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> IO: ...  # noqa: A001
def open(path: str | Path, mode: str = 'r', encoding: str | None = 'utf8', **kwargs: Any):  # noqa: A001
	'Open a file using pathlib.Path.open, with str or Path as path.'
	if isinstance(path, str):
		path = Path(path)
	if 'b' in mode:
		encoding = None
	return path.open(mode, encoding=encoding, **kwargs)

def rmap(
	obj: Any, val_func: Callable | None = None, key_func: Callable | None = None,
	_dict: type[Mapping] | None = None, _list: type[Sequence] | None = None, _sequence: type | tuple[type, ...] = (list, tuple, set, frozenset),
	val_func_extra: bool = False, key_func_extra: bool = False,
) -> Any:
	'''Recursively inplace run functions on key, values, and items of a dict or list.

	Args:
		obj: The list/dict to call funcs on
		val_func: the function to call on each non list/dict object (the stuff in lists and dicts)
		key_func: the function to call on each key in dicts
		_dict: function to convert dicts to
		_list: function to convert lists to, eg. after converting each item in list, convert the list to tuple
		_sequence: what counts as a list, eg. yes sets but not str
		val_func_extra: should the key be passed to the val_func
		key_func_extra: should the val be passed to the key_func

	'''
	self = wrap(rmap, val_func=val_func, key_func=key_func, _list=_list, _dict=_dict, _sequence=_sequence, val_func_extra=val_func_extra, key_func_extra=key_func_extra)
	# if object is a list, call self on each item
	if isinstance(obj, _sequence):
		new = [self(item) for item in obj]
		# if mutable and _list not specified, make change in place
		if isinstance(obj, MutableSequence) and _list is None:
			obj[:] = new
			return obj
		# else, convert new list to _list
		if _list is None:
			_list = type(obj)
		return _list(new)
	# if object is a dict, call self on each value, and key_func on each key
	if isinstance(obj, Mapping):
		if key_func:
			if key_func_extra:
				new = {key_func(key, value): self(value) for key, value in obj.items()}
			else:
				new = {key_func(key): self(value) for key, value in obj.items()}
		else:
			new = {key: self(value) for key, value in obj.items()}
		# if mutable and _dict not specified, make change in place
		if isinstance(obj, MutableMapping):
			obj.clear()
			obj.update(new)
			return obj
		# else, convert new dict to _dict
		if _dict is None:
			_dict = type(obj)
		return _dict(new)
	# if object is neither, call val_func on it
	return (val_func(obj, key) if val_func_extra else val_func(obj)) if val_func else obj

def call(*args: Callable) -> None:
	for arg in args:
		arg()
async def acall(*args: Callable[..., Any]) -> None:
	for arg in args:
		result = arg()
		if inspect.isawaitable(result):
			await result

@contextmanager
def timer(message: str = 'Time elapsed: {:.6f} seconds') -> Generator:
	'''To be used with `with` to time a block of code.

	Yields a handle whose `.elapsed` holds the duration (set when the block exits,
	even if it raises).

	Example:
	```python
	with timer() as t:
		pass  # some code
	time = t.elapsed
	```

	'''
	handle = SimpleNamespace(elapsed=None)
	start = perf_counter()
	try:
		yield handle
	finally:
		handle.elapsed = perf_counter() - start
		print(message.format(handle.elapsed))

class Tee(io.TextIOBase):
	'''Text stream that writes to multiple underlying streams.

	Each target can be:
		* an existing text IO object (for example sys.stdout)
		* a str or Path, which is opened as a file

	If pretend_tty is True, isatty() returns True so color aware
	libraries keep escape codes.
	'''

	def __init__(self, *targets: TextIO | str | Path, isatty: bool = True) -> None:
		super().__init__()
		self._isatty: bool = isatty
		self._owned: list[TextIO] = []  # streams Tee opened itself and is responsible for closing
		self.streams: list[TextIO] = []

		# "open" each str targets
		for target in targets:
			if isinstance(target, (str, Path)):
				target = open(target, 'w')
				self._owned.append(target)
			self.streams.append(target)

		atexit.register(self.close)
	def write(self, s: str) -> int:
		if self.closed:
			raise ValueError('I/O operation on closed file.')
		for stream in self.streams:
			if not getattr(stream, 'closed', False):
				stream.write(s)
				stream.flush()
		return len(s)
	def flush(self) -> None:
		super().flush()
		for stream in self.streams:
			if not getattr(stream, 'closed', False):
				stream.flush()
	def close(self) -> None:
		if self.closed:
			return
		try:
			super().close()
		finally:
			for stream in self._owned:
				if not stream.closed:
					stream.close()
	def isatty(self) -> bool:
		return self._isatty
	def writable(self) -> bool:
		return True
def stdtee(*targets: TextIO | str | Path, isatty: bool = True) -> Tee:
	'''Create a Tee that writes stdout and stderr to sys.stdout and the given targets.'''
	tee = Tee(sys.__stdout__, *targets, isatty=isatty)  # pyright: ignore[reportArgumentType]
	sys.stdout = sys.stderr = tee
	return tee

class Pointer:
	def __init__(self, target: Any = None) -> None:
		self._t: Any = target
	def __getattr__(self, attr: str) -> Any:
		if attr == '_t':
			return super().__getattribute__(attr)
		# so rich doesn't end up causing vscode debug to pause
		if attr in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			return self._t.__getattribute__(attr)  # @IgnoreException
		return getattr(self._t, attr)
	def __setattr__(self, attr: str, value: Any) -> None:
		if attr == '_t':
			super().__setattr__(attr, value)
		else:
			self._t.__setattr__(attr, value)
	def __call__(self, *args: Any, **kwargs: Any) -> Any:
		return self._t(*args, **kwargs)
