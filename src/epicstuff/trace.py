import os, sys
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


enable_locals = False
_install = wrap(install, suppress=[sys.modules[__name__]])
_console = Console()
_install(show_locals=enable_locals, width=_term_width())

def show_local(enable: bool | None = True) -> None:
	global enable_locals
	enable_locals = enable

	_install(show_locals=enable_locals, width=_term_width())


def rich_trace(func: callable = None, show_locals: bool | None = None, _raise: bool = True, _return: Any = None) -> callable:
	@wrapt.decorator
	def wrapper(wrapped, instance, args, kwargs):
		try:
			return wrapped(*args, **kwargs)
		except KeyboardInterrupt:  # pylint: disable=try-except-raise
			raise
		except Exception:  # pylint: disable=broad-except
			_console.print_exception(show_locals=show_locals or enable_locals, width=_term_width(), suppress=[sys.modules[__name__]])
			if _raise:
				raise
			return _return
	if func is None:
		return lambda f: wrapper(f)
	return wrapper(func)


rich_try = wrap(rich_trace, _raise=False)
rich_except = wrap(rich_trace, _raise=True)
