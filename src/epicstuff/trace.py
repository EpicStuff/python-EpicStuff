import inspect, os, sys, atexit
from collections.abc import Awaitable, Callable
from functools import wraps
from types import TracebackType
from typing import Any, ParamSpec, Self, TypeVar, overload, IO
from pathlib import Path

import rich
from rich.console import Console
from rich.traceback import install

from .stuff import Pointer
from .dict import Dict

P = ParamSpec('P')
R = TypeVar('R')


def _term_width(default: int = 160) -> int:
	'''Return terminal width or a sensible default.'''
	try:
		return os.get_terminal_size().columns  # real terminal width
	except OSError:
		return default  # fallback when no TTY
def update_trace(show_locals: bool | None = None, **kwargs) -> None:
	'''Enable or disable showing locals in traceback.'''
	_trace_kwargs.update(kwargs)

	if show_locals is not None:
		_trace_kwargs.show_locals = show_locals

	install(**_trace_kwargs)
def update_console(file: str | IO | None = None, **kwargs) -> None | IO:
	_console_kwargs.update(kwargs)

	if file:
		if isinstance(file, str):
			file = Path(file).open('w', encoding='utf8')  # noqa: SIM115
		_console_kwargs.file = file

		@atexit.register
		def _close_log() -> None:
			file.flush()
			file.close()

	rich.reconfigure(**_console_kwargs)
	console._t = Console(**_console_kwargs)  # pyright: ignore[reportArgumentType] # noqa: SLF001
	return file  # pyright: ignore[reportReturnType]
def install_trace(show_locals: bool | None = None, file: str | IO | None = None, trace_kwargs: dict | None = None, console_kwargs: dict | None = None) -> None | IO:
	'''Install global traceback.'''
	update_trace(show_locals, **(trace_kwargs or {}))
	file = update_console(file, **(console_kwargs or {}))

	install(**_trace_kwargs)

	return file


# default args
_console_kwargs = Dict({'tab_size': 4}, _convert=False)
_trace_kwargs = Dict({'show_locals': True, 'locals_max_length': 24, 'width': _term_width(), 'suppress': [sys.modules[__name__]]}, _convert=False)
rich.reconfigure(**_console_kwargs)

console = Pointer(Console(**_console_kwargs))


class _RichTrace:
	'''Wrapper around Rich's traceback.

	Can be used as both a decorator and a context manager.
	- As a decorator: @rich_trace or @rich_trace(...)
	- As a context manager: with rich_trace: ... or with rich_trace(...): ...
	'''

	def __init__(self, show_locals: bool | None = None, _raise: bool | None = True, _return: Any = None) -> None:
		self._show = show_locals
		self._raise = _raise
		self._return = _return

	# runs instance is called as a function (with `with` or `@`)
	@overload
	def __call__(self, func: Callable[P, R], /) -> Callable[P, R]: ...
	@overload
	def __call__(self, /, **opts: Any) -> Self: ...
	def __call__(self, func: Callable | None = None, /, **opts: Any) -> Callable | Self:
		'''Support both decorator and context manager config.

		- If passed a function (no options), decorate it using current config.
		- Otherwise, return a configured instance for @rich_trace(...) or with rich_trace(...):
		'''
		# If bare callable provided (e.g., @rich_trace), wrap immediately using current config
		if callable(func) and not opts:
			# choose async or sync wrapper based on coroutine-ness
			if inspect.iscoroutinefunction(func):
				return self._wrap_async(func)
			return self._wrap_sync(func)

		# Build a configured instance (for @rich_trace(...)) or (with rich_trace(...):)
		return _RichTrace(show_locals=opts.get('show_locals', self._show), _raise=opts.get('_raise', self._raise), _return=opts.get('_return', self._return))

	def _handle_exc(self, exc: BaseException) -> Any:
		'''Handle exception according to configuration.

		`_raise=True`:  print then re-raise
		`_raise=None`:  print then return `_return`
		`_raise=False`: just return `_return`
		'''
		if self._raise is not False:
			console.print_exception(**_trace_kwargs)
		if self._raise:
			raise exc
		return self._return

	def _wrap_sync(self, wrapped: Callable[..., Any]) -> Callable[..., Any]:
		'''Wrap a sync function.'''
		@wraps(wrapped)
		def _sync(*_args: Any, **_kwargs: Any) -> Any:
			try:
				return wrapped(*_args, **_kwargs)
			except Exception as _exc:  # pylint: disable=broad-except  # noqa: BLE001
				return self._handle_exc(_exc)
		return _sync

	def _wrap_async(self, wrapped: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
		'''Wrap an async function.'''
		@wraps(wrapped)
		async def _async(*_args: Any, **_kwargs: Any) -> Any:
			try:
				return await wrapped(*_args, **_kwargs)
			except Exception as _exc:  # pylint: disable=broad-except  # noqa: BLE001
				return self._handle_exc(_exc)
		return _async

	# Context manager usage
	def __enter__(self) -> Self:
		return self

	def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, _tb: TracebackType | None) -> bool:
		# No exception: do nothing
		if exc is None:
			return False
		# Yes exception: print
		if exc_type is not None:
			try:
				self._handle_exc(exc)
			# re-raise path: do not suppress
			except exc_type:
				return False
			# suppressed path: tell context manager to suppress
			return True
		# Fallback: if exc_type is None, don't suppress
		return False


# Public instances (dual-usage: decorator and context manager)
rich_trace = _RichTrace()
rich_try = _RichTrace(_raise=None)
