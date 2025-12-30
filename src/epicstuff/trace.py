import atexit, contextvars, inspect, io, os, sys
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Any, ParamSpec, Self, TypeVar, overload

import rich
from rich.console import Console
from rich.traceback import Traceback, install

from .dict import Dict
from .stuff import Pointer

P = ParamSpec('P')
R = TypeVar('R')


# Per-exception render context for objects' __repr__ to consult.
_active_trace_kwargs: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar('_RichTrace', default=None)

def get_trace_kwargs() -> dict[str, Any]:
	'Return the currently active traceback render kwargs.'
	return _active_trace_kwargs.get() or _trace_kwargs


def _term_width(default: int = 160) -> int:
	'Return terminal width or a sensible default.'
	try:
		return os.get_terminal_size().columns  # real terminal width
	except OSError:
		return default  # fallback when no TTY
def update_trace(show_locals: bool | None = None, **kwargs) -> None:
	'Enable or disable showing locals in traceback.'
	_trace_kwargs.update(kwargs)

	if show_locals is not None:
		_trace_kwargs.show_locals = show_locals

	install(**_trace_kwargs)
def update_console(file: str | io.IOBase | None = None, **kwargs) -> None | io.IOBase:
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
	console._t = Console(**_console_kwargs)  # pyright: ignore[reportArgumentType]
	return file  # pyright: ignore[reportReturnType]
def install_trace(show_locals: bool | None = None, file: str | io.IOBase | None = None, trace_kwargs: dict | None = None, console_kwargs: dict | None = None) -> None | io.IOBase:
	'''Install global traceback.'''
	update_trace(show_locals, **(trace_kwargs or {}))
	file = update_console(file, **(console_kwargs or {}))

	install(**_trace_kwargs)

	return file


# default args
_console_kwargs = Dict({'tab_size': 4}, _convert=False)
_trace_kwargs = Dict({'show_locals': True, 'locals_max_length': 16, 'width': _term_width(), 'suppress': [sys.modules[__name__]]}, _convert=False)
rich.reconfigure(**_console_kwargs)

console = Pointer(Console(**_console_kwargs))


class _RichTrace:
	'''Wrapper around Rich's traceback.

	Can be used as both a decorator and a context manager.
	- As a decorator: @rich_trace or @rich_trace(...)
	- As a context manager: with rich_trace: ... or with rich_trace(...): ...

	Raise:
		`_raise=True`:  print then re-raise
		`_raise=None`:  print then return `_return`
		`_raise=False`: just return `_return`

	'''

	def __init__(self, show_locals: bool | None = None, _raise: bool | None = True, _return: Any = None, **trace_kwargs) -> None:
		self._raise = _raise
		self._return = _return
		self.kwargs = trace_kwargs | ({'show_locals': show_locals} if show_locals is not None else {})

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
		return _RichTrace(**(self.kwargs | {'_raise': self._raise, '_return': self._return} | opts))

	def _handle_exc(self, exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> Any:
		'''Handle exception according to configuration.

		`_raise=True`:  print then re-raise
		`_raise=None`:  print then return `_return`
		`_raise=False`: just return `_return`
		'''
		if self._raise is not False:
			# get the trace kwargs for this context and token
			context_kwargs = _trace_kwargs | self.kwargs
			token = _active_trace_kwargs.set(context_kwargs)
			# pretty print the traceback
			try:
				console.print(
					Traceback.from_exception(
						exc_type,
						exc,
						tb,
						**context_kwargs,
					),
				)
			# make sure to reset the trace kwarg
			finally:
				_active_trace_kwargs.reset(token)
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
				return self._handle_exc(type(_exc), _exc, _exc.__traceback__)
		return _sync

	def _wrap_async(self, wrapped: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
		'''Wrap an async function.'''
		@wraps(wrapped)
		async def _async(*_args: Any, **_kwargs: Any) -> Any:
			try:
				return await wrapped(*_args, **_kwargs)
			except Exception as _exc:  # pylint: disable=broad-except  # noqa: BLE001
				return self._handle_exc(type(_exc), _exc, _exc.__traceback__)
		return _async

	# Context manager usage
	def __enter__(self) -> Self:
		return self
	async def __aenter__(self) -> Self:
		return self.__enter__()

	def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> bool:
		# No exception: do nothing
		if exc is None:
			return False
		# Yes exception: print
		if exc_type is not None:
			try:
				self._handle_exc(exc_type, exc, tb)
			# re-raise path: do not suppress
			except exc_type:
				return False
			# suppressed path: tell context manager to suppress
			return True
		# Fallback: if exc_type is None, don't suppress
		return False
	async def __aexit__(self, *args: object) -> bool:
		return self.__exit__(*args)


# Public instances (dual-usage: decorator and context manager)
rich_trace = _RichTrace()
rich_try = _RichTrace(_raise=None)
