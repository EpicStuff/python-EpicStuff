from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, overload

from .dict import BoxDict, Dict, JDict, NewDict
from .fix_import import fix_import
from .permissify import permissify as perm
from .progress import Bar
from .s import String as s
from .stuff import Pointer, Tee, acall, call, open, rmap, stdtee, timer, wrap  # noqa: A004  # pylint: disable=redefined-builtin
from .sudo import sudo
from .trace import console, get_trace_kwargs, install_trace, rich_trace, rich_try, update_console, update_trace
from .version import __version__ as __version__  # pylint: disable=useless-import-alias

if TYPE_CHECKING:
	# Advertise dynamically-provided attributes for static analyzers
	def run_install_trace() -> None: ...
	def run_fix_import() -> None: ...

OldDict = Dict

__all__ = [
	'Bar',
	'BoxDict',
	'Dict',
	'JDict',
	'NewDict',
	'OldDict',
	'Pointer',
	'Tee',
	'acall',
	'call',
	'console',
	'get_trace_kwargs',
	'install_trace',
	'open',
	'perm',
	'rich_trace',
	'rich_try',
	'rmap',
	'run_fix_import',
	'run_install_trace',
	's',
	'stdtee',
	'sudo',
	'timer',
	'update_console',
	'update_trace',
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
