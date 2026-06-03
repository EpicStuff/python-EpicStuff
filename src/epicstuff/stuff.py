import atexit, inspect, io, sys
from collections.abc import Callable, Mapping, MutableSequence, MutableMapping, Sequence
from functools import partial as wrap
from pathlib import Path
from typing import IO, Any


def open(path: str | Path, mode: str = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> IO:  # noqa: A001
	'Open a file using pathlib.Path.open, with str or Path as path.'
	if isinstance(path, str):
		path = Path(path)
	if 'b' in mode:
		encoding = None
	return path.open(mode, encoding=encoding, **kwargs)

def rmap(
	obj: Any, val_func: Callable | None = None, key_func: Callable | None = None,
	_dict: type[Mapping] | None = None, _list: type[Sequence] | None = None, _sequence: type | tuple[type, ...] = (list, tuple, set, frozenset),
	) -> Any:
	'Recursively run functions on key, values, and items of a dict or list.'
	self = wrap(rmap, val_func=val_func, key_func=key_func, _list=_list, _dict=_dict, _sequence=_sequence)
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
		new = {key_func(key) if key_func else key: self(value) for key, value in obj.items()}
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
	return val_func(obj) if val_func else obj

def call(*args: Callable) -> None:
	for arg in args:
		arg()
async def acall(*args: Callable[..., Any]) -> None:
	for arg in args:
		result = arg()
		if inspect.isawaitable(result):
			await result

class Tee(io.TextIOBase):
	'''Text stream that writes to multiple underlying streams.

	Each target can be:
		* an existing text IO object (for example sys.stdout)
		* a str or Path, which is opened as a file

	If pretend_tty is True, isatty() returns True so color aware
	libraries keep escape codes.
	'''

	def __init__(self, *targets: IO | str, isatty: bool = True) -> None:  # pyright: ignore[reportRedeclaration]
		super().__init__()
		targets: list = list(targets)
		for index, target in enumerate(targets):
			if isinstance(target, str):
				targets[index] = Path(target).open('w', encoding='utf8')  # noqa: SIM115
				atexit.register(targets[index].close)

		self.streams = targets
		self._isatty = isatty
	def write(self, s: str) -> int:
		for stream in self.streams:
			stream.write(s)
			stream.flush()
		return len(s)
	def flush(self) -> None:
		for stream in self.streams:
			stream.flush()
	def isatty(self) -> bool:
		return self._isatty
	def writable(self) -> bool:
		return True
def stdtee(*targets: IO | str, isatty: bool = True) -> Tee:
	'''Create a Tee that writes stdout and stderr to sys.stdout and the given targets.'''
	tee = Tee(sys.stdout, *targets, isatty=isatty)
	sys.stdout = sys.stderr = tee
	return tee

class Pointer:
	def __init__(self, target: Any = None) -> None:
		self._t = target
	def __getattr__(self, attr: str) -> Any:
		if attr == '_t':
			return super().__getattribute__(attr)
		# so rich doesn't end up causing vscode debug to pause
		if attr in ('awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492', '__rich_repr__', '_fields'):
			return self._t.__getattribute__(attr)  # @IgnoreException
		return self._t.__getattribute__(attr)
	def __setattr__(self, attr: str, value: Any) -> None:
		if attr == '_t':
			super().__setattr__(attr, value)
		else:
			self._t.__setattr__(attr, value)
	def __call__(self, *args: Any, **kwargs: Any) -> Any:
		return self._t(*args, **kwargs)
