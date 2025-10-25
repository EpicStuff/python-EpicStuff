import inspect
import sys
from pathlib import Path


def _path_in_syspath(dirpath: Path) -> bool:
	'''Returns if an equivalent directory is already in sys.path'''
	dirpath = dirpath.resolve()
	for p in sys.path:
		try:
			if Path(p).resolve() == dirpath:
				return True
		except Exception:  # noqa: BLE001, PERF203, S112, RUF100  # pylint: disable=broad-exception-caught  # trunk-ignore(bandit/B112)
			continue
	return False

def fix_import() -> str | None:
	'''Locate importer and append its directory to sys.path if not already present.'''
	for frame_info in inspect.stack():
		mod = inspect.getmodule(frame_info.frame)
		if mod is None:
			continue
		name = getattr(mod, '__name__', '')
		# our own frames, keep searching
		if name.startswith('epicstuff'):
			continue
		# import system frames, keep searching  # ruff: noqa: ERA001
		if name.startswith('importlib'):
			continue
		# no filesystem location, keep searching
		filename = getattr(mod, '__file__', None)
		if not filename:
			continue

		dirpath = Path(filename).resolve().parent
		# if not already present
		if not _path_in_syspath(dirpath):
			sys.path.insert(0, str(dirpath))
			return str(dirpath)
		print('Failed to "fix import"')
		return None
	print('Failed to "fix import"')
	return None
