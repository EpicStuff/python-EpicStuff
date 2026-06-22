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

def _resolve_root(root: str, filepath: Path) -> Path:
	'Resolve a `root` argument to an absolute directory that must be an ancestor of `filepath`.'
	# root looks like a path (has a separator or leading dot) vs a bare ancestor name
	if root.startswith('.') or '/' in root or '\\' in root:
		root_path = Path(root)
		# relative paths (incl. leading-dot) resolve against the importer file, like '..'
		if not root_path.is_absolute():
			root_path = filepath.parent / root_path
		root_dir = root_path.resolve()
	else:
		# bare name: find the nearest ancestor directory with that name
		root_dir = next((p for p in filepath.parents if p.name == root), None)
		if root_dir is None:
			raise ImportError(f'fix_import: no ancestor directory named {root!r} above {filepath}')
	if not (root_dir == filepath.parent or root_dir in filepath.parents):
		raise ImportError(f'fix_import: {root!r} (resolved to {root_dir}) is not a parent directory of {filepath}')
	return root_dir

def _autodetect_root(filepath: Path) -> Path:
	'Walk up from the importer file while `__init__.py` markers continue, returning the top package directory.'
	pkg_dir = filepath.parent
	# climb while the directory above is also a package
	while (pkg_dir.parent / '__init__.py').is_file():
		pkg_dir = pkg_dir.parent
	return pkg_dir

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
		# if root not provided, auto-detect the package root (falls back to the file's own dir)
		if root is None:
			root_dir = _autodetect_root(filepath)
		# else resolve the given root (name, dotted path, or absolute) to an ancestor dir
		else:
			root_dir = _resolve_root(root, filepath)
		dirpath = root_dir.parent
		package_name = '.'.join([root_dir.name, *filepath.parent.relative_to(root_dir).parts])
		# if not already present
		if not _path_in_syspath(dirpath):
			sys.path.insert(0, str(dirpath))
		mod.__package__ = package_name
		return
	raise ImportError('fix_import: could not locate the importing module on the call stack')
