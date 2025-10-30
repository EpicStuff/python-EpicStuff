'''Wrapper around Rich's traceback..'''

import os, sys, inspect
from functools import wraps
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.traceback import install


def _term_width(default: int = 160) -> int:
	'''Return terminal width or a sensible default.'''
	try:
		return os.get_terminal_size().columns  # real terminal width
	except OSError:
		return default  # fallback when no TTY


_enable_locals = True  # global default for showing locals in tracebacks
def enable_locals(show_locals: bool = True) -> None:
	'''Function to enable or disable showing locals in traceback.'''
	global _enable_locals
	_enable_locals = show_locals
def install_trace(show_locals: bool | None = None) -> None:
	'''Install global traceback.'''
	install(show_locals=show_locals or _enable_locals, width=_term_width(), suppress=[sys.modules[__name__]])


class _RichTry:
	'''Object that can be used as both a decorator and a context manager.

	- As a decorator: @rich_trace or @rich_trace(...)
	- As a context manager: with rich_trace: ... or with rich_trace(...): ...
	'''

	_console = Console()

	def __init__(self, show_locals: bool | None = None, _raise: bool = False, _return: Any = None) -> None:
		self._show = show_locals
		self._raise = _raise
		self._return = _return

	# runs instance is called as a function (with `with` or `@`)
	def __call__(self, func: Callable | None = None, /, **opts: Any):
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
		return _RichTry(show_locals=opts.get('show_locals', self._show), _raise=opts.get('_raise', self._raise), _return=opts.get('_return', self._return))

	def _handle_exc(self, exc: Exception) -> Any:
		# print and either re-raise or return default
		self._console.print_exception(show_locals=_enable_locals if self._show is None else self._show, width=_term_width(), suppress=[sys.modules[__name__]])
		if self._raise:
			raise exc
		return self._return

	def _wrap_sync(self, wrapped: Callable) -> Callable:
		'''Wrap a sync function.'''
		@wraps(wrapped)
		def _sync(*_args, **_kwargs) -> Any:
			try:
				return wrapped(*_args, **_kwargs)
			except Exception as _exc:  # pylint: disable=broad-except  # noqa: BLE001
				return self._handle_exc(_exc)
		return _sync

	def _wrap_async(self, wrapped: Callable) -> Callable:
		'''Wrap an async function.'''
		@wraps(wrapped)
		async def _async(*_args, **_kwargs) -> Any:
			try:
				return await wrapped(*_args, **_kwargs)
			except Exception as _exc:  # pylint: disable=broad-except  # noqa: BLE001
				return self._handle_exc(_exc)
		return _async

	# Context manager usage
	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc, _tb) -> bool:
		# No exception: do nothing
		if exc is None:
			return False
		# Yes exception: print
		try:
			self._handle_exc(exc)
		# re-raise path: do not suppress
		except exc_type:
			return False
		# suppressed path: tell context manager to suppress
		return True


# Public instances (dual-usage: decorator and context manager)
rich_try = _RichTry()
rich_except = _RichTry(_raise=True)
rich_trace = _RichTry(_raise=True)
