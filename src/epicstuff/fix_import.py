import inspect, sys
from pathlib import Path


def _path_in_syspath(dirpath: Path) -> bool:
	'Return if an equivalent directory is already in `sys.path`.'
	dirpath = dirpath.resolve()
	for p in sys.path:
		try:
			if Path(p).resolve() == dirpath:
				return True
		except Exception:  # noqa: BLE001, S112
			continue
	return False

def fix_import(root: str | None = None) -> None:
	'Locate importer, update sys.path, and set package for relative imports.'
	for frame_info in inspect.stack():
		# get fix_import caller
		mod = inspect.getmodule(frame_info.frame)
		if mod is None:
			continue
		name = getattr(mod, '__name__', '')
		## our own frames, keep searching
		if name.startswith('epicstuff'):
			continue
		## import system frames, keep searching
		if name.startswith('importlib'):
			continue
		## no filesystem location, keep searching
		filename = getattr(mod, '__file__', None)
		if not filename:
			continue

		filepath = Path(filename).resolve()
		# if root not provided, use importer file parent as root
		if root is None:
			dirpath = filepath.parents[1]
			package_name = None
		else:
			# if root is path, if is relative , resolve from importer file location
			if root.startswith('.') or '/' in root or '\\' in root:
				root_dir = (filepath.parent / root).resolve() if root.startswith('.') else Path(root)
			# else, find folder with same name as root in importer file parents
			else:
				root_dir = next((p for p in filepath.parents if p.name == root), None)
				if root_dir is None:
					print('Failed to "fix import"')
					return
			dirpath = root_dir.parent
			package_name = '.'.join([root_dir.name, *filepath.parent.relative_to(root_dir).parts])
		# if not already present
		if not _path_in_syspath(dirpath):
			sys.path.insert(0, str(dirpath))
		if package_name is not None:
			mod.__package__ = package_name
		return
	print('Failed to "fix import"')
	return
