import inspect, sys
from pathlib import Path
from typing import Literal, TYPE_CHECKING

from beartype import beartype

if TYPE_CHECKING:
	from types import FrameType


@beartype
def fix_import(root: str | Path | None = None, relative: Literal['file', 'cwd'] = 'file') -> None:  # pyright: ignore[reportRedeclaration]
	'''Locate importer, update `sys.path`, and set `__package__` for relative imports.

	Args:
		`root`: Package root as a directory name or path. If omitted, detect it from the caller.
		`relative`: Resolve relative root *paths* against the caller file or current working directory.
			Only affects `root` values that are relative paths; ignored for bare names and absolute paths.

	'''
	frame: FrameType = inspect.currentframe()  # pyright: ignore[reportRedeclaration]

	while True:
		frame: FrameType | None = frame.f_back
		if frame is None:
			raise ImportError('fix_import: could not locate the importing module on the call stack')
		globals_ = frame.f_globals
		name: str = globals_.get('__name__', '') or ''

		## beartype (and similar) wrappers have no module name, keep searching
		if not name:
			continue
		## our own frames, keep searching
		if name == 'epicstuff' or name.startswith('epicstuff.'):
			continue
		## import system frames, keep searching
		if name == 'importlib' or name.startswith(('importlib.', '_frozen_importlib')):
			continue

		## found caller
		filename: str | None = globals_.get('__file__')
		# angle-bracket names (<stdin>, <string>, <ipython-input-…>) aren't real paths
		if filename and not (filename.startswith('<') and filename.endswith('>') and not Path(filename).exists()):
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
		# a Path is always a path; a str may be a path or a bare ancestor name
		if isinstance(root, Path) or root.startswith(('.', '~')) or '/' in root or '\\' in root or (root := Path(root)).is_absolute() or root.drive:  # pylint: disable=no-member,unsupported-membership-test
			root = Path(root).expanduser()
			# relative paths resolve against the importer file or cwd
			if not root.is_absolute():
				root = (caller_dir if relative == 'file' else Path.cwd()) / root
			root = root.resolve()
			if not root.is_dir():
				raise ImportError(f'fix_import: root directory does not exist: {root}')
		# else, a bare name, find the nearest ancestor directory with that name
		else:
			try:
				root = next(ancestor for ancestor in (caller_dir, *caller_dir.parents) if ancestor.name == str(root))
			except StopIteration:
				raise ImportError(f'fix_import: no ancestor directory named {root} above {caller_dir}') from None

		# with relative='cwd' the root need not be an ancestor of the caller file
		if relative == 'file' and filepath is not None and root not in filepath.parents:
			raise ImportError(f'fix_import: resolved to {root}, is not a parent directory of {filepath}')

	dirpath = root.parent

	# a notebook or cwd-relative root can be outside the caller dir and belong directly to the root package
	if root != caller_dir and root not in caller_dir.parents:
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
