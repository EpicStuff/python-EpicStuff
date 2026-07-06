import inspect, sys
from pathlib import Path
from typing import Literal

from beartype import beartype


@beartype
def fix_import(root: str | None = None, relative: Literal['file', 'cwd'] = 'file') -> None:
	'''Locate importer, update `sys.path`, and set `__package__` for relative imports.

	Args:
		`root`: Package root as a directory name or path. If omitted, detect it from the caller.
		`relative`: Resolve relative root paths from the caller file or current working directory.

	'''
	frame = inspect.currentframe()

	while True:
		frame = frame.f_back
		if frame is None:
			raise ImportError('fix_import: could not locate the importing module on the call stack')
		globals_ = frame.f_globals
		name = globals_.get('__name__', '') or ''

		## our own frames, keep searching
		if name == 'epicstuff' or name.startswith('epicstuff.'):
			continue
		## import system frames, keep searching
		if name == 'importlib' or name.startswith(('importlib.', '_frozen_importlib')):
			continue

		## found caller
		filename = globals_.get('__file__')
		if filename and not (isinstance(filename, str) and filename.startswith('<') and filename.endswith('>') and not Path(filename).exists()):
			filepath = Path(filename).resolve()
			caller_dir = filepath.parent
		else:
			filepath = None
			caller_dir = Path.cwd().resolve()
		break
	del frame

	# if root not provided, auto detect the package root
	if root is None:
		# Walk up from the importer file while `__init__.py` markers continue, returning the top package directory
		root: Path = caller_dir
		# climb while the directory above is also a package
		while (root.parent / '__init__.py').is_file():
			root = root.parent
	# else resolve the given root (name or path) to an ancestor dir
	else:
		# if root looks like a path
		if root.startswith(('.', '~')) or '/' in root or '\\' in root or Path(root).is_absolute() or bool(Path(root).drive):
			root = Path(root).expanduser()
			# relative paths resolve against the importer file or cwd
			if not root.is_absolute():
				root = (caller_dir if relative == 'file' else Path.cwd()) / root
			root = root.resolve()
			if not root.is_dir():
				raise ImportError(f'fix_import: root directory does not exist: {root}')
		# else, a name
		else:
			# bare name: find the nearest ancestor directory with that name
			try:
				root = next(p for p in (caller_dir, *caller_dir.parents) if p.name == root)
			except StopIteration:
				raise ImportError(f'fix_import: no ancestor directory named {root!r} above {caller_dir}') from None

		if filepath is not None and root not in filepath.parents:
			raise ImportError(f'fix_import: resolved to {root}, is not a parent directory of {filepath}')

	dirpath = root.parent

	# A notebook can be outside the package directory and belong directly to the root package
	if filepath is None and root != caller_dir and root not in caller_dir.parents:
		package_name = root.name
	else:
		package_name = '.'.join([root.name, *caller_dir.relative_to(root).parts])

	# if dirpath not already present
	for path in sys.path:
		try:
			if Path(path).resolve() == dirpath:
				break
		except (OSError, RuntimeError):
			continue
	else:
		sys.path.insert(0, str(dirpath))

	globals_['__package__'] = package_name
