import os, sys
from collections.abc import Callable
from typing import Any

import wrapt
from rich.console import Console
from rich.traceback import install

from .stuff import wrap


def _term_width(default: int = 100) -> int:
	try:
		return os.get_terminal_size().columns
	except OSError:
		return default
_enable_locals = True
def enable_locals(show_locals: bool = True) -> None:
	global _enable_locals
	_enable_locals = show_locals
def install_trace(show_locals: bool | None = None) -> None:
	install(show_locals=show_locals or _enable_locals, width=_term_width(), suppress=[sys.modules[__name__]])


def rich_trace(func: Callable | None = None, show_locals: bool | None = None, _raise: bool = True, _return: Any = None) -> Callable:
	@wrapt.decorator
	def wrapper(wrapped: Callable, _instance: object | None, _args: tuple, _kwargs: dict) -> Any:
		try:
			return wrapped(*_args, **_kwargs)
		except KeyboardInterrupt:  # pylint: disable=try-except-raise
			raise
		except Exception:  # pylint: disable=broad-except
			_console.print_exception(show_locals=show_locals or _enable_locals, width=_term_width(), suppress=[sys.modules[__name__]])
			if _raise:
				raise
			return _return
	if func is None:
		return wrapper
	return wrapper(func)  # type: ignore[reportCallIssue]  # pylint: disable=E1120


_console = Console()
rich_try = wrap(rich_trace, _raise=False)
rich_except = wrap(rich_trace, _raise=True)
