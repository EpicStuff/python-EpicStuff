import inspect, sys
from pathlib import Path


def fix_import(root: str | None = None) -> None:
	'Locate importer, update `sys.path`, and set `__package__` for relative imports.'
	for frame_info in inspect.stack(context=0):
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

		## found caller
		filepath = Path(filename).resolve()
		break
	else:
		raise ImportError('fix_import: could not locate the importing module on the call stack')

	# if root not provided, auto-detect the package root
	if root is None:
		# Walk up from the importer file while `__init__.py` markers continue, returning the top package directory
		root: Path = filepath.parent
		# climb while the directory above is also a package
		while (root.parent / '__init__.py').is_file():
			root = root.parent
	# else resolve the given root (name or path) to an ancestor dir
	else:
		# if root looks like a path (has a separator or leading dot)
		if root.startswith('.') or '/' in root or '\\' in root:
			root = Path(root).expanduser()
			# relative paths (incl. leading-dot) resolve against the importer file
			if not root.is_absolute():
				root = filepath.parent / root
			root = root.resolve()
		# else, a name
		else:
			# bare name: find the nearest ancestor directory with that name
			try:
				root = next(p for p in filepath.parents if p.name == root)
			except StopIteration:
				raise ImportError(f'fix_import: no ancestor directory named {root!r} above {filepath}') from None
		if root not in filepath.parents:
			raise ImportError(f'fix_import: resolved to {root}, is not a parent directory of {filepath}')

	dirpath = root.parent
	package_name = '.'.join([root.name, *filepath.parent.relative_to(root).parts])

	# if dirpath not already present
	for path in sys.path:
		try:
			if Path(path).resolve() == dirpath:
				break
		except Exception:
			continue
	else:
		sys.path.insert(0, str(dirpath))
	mod.__package__ = package_name
