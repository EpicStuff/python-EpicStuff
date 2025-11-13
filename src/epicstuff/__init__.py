from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, overload

from .dict import Dict
from .fix_import import fix_import
from .permissify import permissify as perm
from .progress import Bar
from .s import String as s  # noqa: N813
from .stuff import open, rmap, wrap  # noqa: A004  # pylint: disable=redefined-builtin
from .timer import timer
from .trace import enable_locals as show_locals, install_trace, rich_trace, rich_try
from .version import __version__ as __version__  # pylint: disable=useless-import-alias

if TYPE_CHECKING:
	# Advertise dynamically-provided attributes for static analyzers
	def run_install_trace() -> None: ...
	def run_fix_import() -> None: ...

__all__ = [
	'Bar',
	'Dict',
	'install_trace',
	'open',
	'perm',
	'rich_trace',
	'rich_try',
	'rmap',
	'run_fix_import',
	'run_install_trace',
	's',
	'show_locals',
	'timer',
	'wrap',
]

@overload
def __getattr__(name: Literal['run_install_trace']) -> Callable: ...
@overload
def __getattr__(name: Literal['run_fix_import']) -> None: ...
def __getattr__(name: str) -> Callable | None:
	if name == 'run_install_trace':
		install_trace()
		return install_trace
	if name == 'run_fix_import':
		fix_import()
		return None
	msg = f'module epicstuff has no attribute {name!r}'
	raise AttributeError(msg)
