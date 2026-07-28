import enum, io
from collections.abc import Callable, Generator, Mapping, Sequence, Set
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, BinaryIO, Final, TextIO, overload

from _typeshed import FileDescriptorOrPath, OpenBinaryMode, OpenBinaryModeReading, OpenBinaryModeUpdating, OpenBinaryModeWriting, OpenTextMode


type List[a] = list[a] | tuple[a, ...]
class _Unset(enum.Enum): UNSET = enum.auto()
_unset: Final = _Unset.UNSET  # a none thats not none
type Op[O] = O | _Unset  # optional (with unset)

@overload
def open(path: FileDescriptorOrPath, mode: OpenTextMode = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> io.TextIOWrapper: ...  # noqa: A001
@overload
def open(path: FileDescriptorOrPath, mode: OpenBinaryModeReading, encoding: None = None, **kwargs: Any) -> io.BufferedReader: ...  # noqa: A001
@overload
def open(path: FileDescriptorOrPath, mode: OpenBinaryModeWriting, encoding: None = None, **kwargs: Any) -> io.BufferedWriter: ...  # noqa: A001
@overload
def open(path: FileDescriptorOrPath, mode: OpenBinaryModeUpdating, encoding: None = None, **kwargs: Any) -> io.BufferedRandom: ...  # noqa: A001
@overload
def open(path: FileDescriptorOrPath, mode: OpenBinaryMode, encoding: None = None, **kwargs: Any) -> BinaryIO: ...  # noqa: A001
@overload
def open(path: FileDescriptorOrPath, mode: str = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> IO[Any]: ...  # noqa: A001
def open(path: str | Path, mode: str = 'r', encoding: str | None = 'utf8', **kwargs: Any) -> IO[Any]: ...  # noqa: A001


def call(*args: Callable) -> None: ...
async def acall(*args: Callable[..., Any]) -> None: ...

@contextmanager
def timer(message: str = 'Time elapsed: {:.6f} seconds') -> Generator: ...

class Tee(io.TextIOBase):
	def __init__(self, *targets: TextIO | str | Path, isatty: bool = True) -> None: ...
	def write(self, s: str) -> int: ...
	def flush(self) -> None: ...
	def close(self) -> None: ...
	def isatty(self) -> bool: ...
	def writable(self) -> bool: ...
def stdtee(*targets: TextIO | str | Path, isatty: bool = True) -> Tee: ...

class Pointer:
	def __init__(self, target: Any = None) -> None: ...
	def __getattr__(self, attr: str) -> Any: ...
	def __setattr__(self, attr: str, value: Any) -> None: ...
	def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
