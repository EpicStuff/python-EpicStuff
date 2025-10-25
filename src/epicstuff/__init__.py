from collections.abc import Callable

from .dict import Dict
from .fix_import import fix_import
from .progress import Bar
from .s import String as s  # noqa: N813
from .stuff import open, wrap  # noqa: A004  # pylint: disable=redefined-builtin
from .timer import timer
from .trace import enable_locals as show_locals, install_trace, rich_except, rich_trace, rich_try
from .version import __version__ as __version__  # pylint: disable=useless-import-alias

__all__ = [
	'Bar',
	'Dict',
	'install_trace',
	'open',
	'rich_except',
	'rich_trace',
	'rich_try',
	's',
	'show_locals',
	'timer',
	'wrap',
]


def __getattr__(name: str) -> Callable | None:
	if name == 'run_install_trace':
		install_trace()
		return install_trace
	if name == 'run_fix_import':
		fix_import()
		return None
	msg = f'module epicstuff has no attribute {name!r}'
	raise AttributeError(msg)
