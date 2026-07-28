import atexit, contextlib, enum, inspect, io, sys, time, types
from collections.abc import Callable, Generator
from pathlib import Path
from typing import IO, Any, BinaryIO, Final, Literal, TextIO, overload


type List[a] = list[a] | tuple[a, ...]
class _Unset(enum.Enum): UNSET = enum.auto()
_unset: Final = _Unset.UNSET  # a none thats not none
type Op[O] = O | _Unset  # optional (with unset)

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

def call(*args: Callable) -> None:
	for arg in args:
		arg()
async def acall(*args: Callable[..., Any]) -> None:
	for arg in args:
		result = arg()
		if inspect.isawaitable(result):
			await result

@contextlib.contextmanager
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
	handle = types.SimpleNamespace(elapsed=None)
	start = time.perf_counter()
	try:
		yield handle
	finally:
		handle.elapsed = time.perf_counter() - start
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
