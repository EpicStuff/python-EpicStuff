import atexit, inspect, io, sys
from collections.abc import Callable
from functools import partial as wrap
from pathlib import Path
from typing import IO, Any

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
