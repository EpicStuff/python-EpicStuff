import subprocess, sys, tempfile
from pathlib import Path

# Script executed AS the importer module (run directly, so __name__ == '__main__',
# the exact situation fix_import is meant to repair).
RUNNER = '''
import sys
sys.path[:0] = {syspath!r}
from epicstuff import fix_import
try:
	fix_import({arg})
except Exception as e:
	print('RAISE', type(e).__name__)
	raise SystemExit
print('PKG', repr(__package__))
for stmt in ['from . import x', 'from .. import y']:
	try:
		exec(stmt)
		print('OK', stmt)
	except Exception as e:
		print('ERR', stmt, type(e).__name__)
'''


def build_tree(base, init):
	'proj/src/a/b/{run.py,x.py} + proj/src/a/y.py, optionally with __init__.py markers.'
	b = base / 'proj' / 'src' / 'a' / 'b'
	b.mkdir(parents=True)
	(b / 'x.py').write_text("VAL = 'x'\n")
	(b.parent / 'y.py').write_text("VAL = 'y'\n")
	if init:
		for d in (base / 'proj' / 'src', base / 'proj' / 'src' / 'a', b):
			(d / '__init__.py').write_text('')
	return b


def run_case(name, arg, init, cwd_rel, expected):
	'Build a fresh tree, run the importer script as a subprocess, assert on its output lines.'
	with tempfile.TemporaryDirectory() as tmp:
		base = Path(tmp)
		b = build_tree(base, init)
		run_py = b / 'run.py'
		run_py.write_text(RUNNER.format(syspath=sys.path, arg=arg))
		cwd = base if cwd_rel is None else base / cwd_rel
		out = subprocess.run([sys.executable, str(run_py)], capture_output=True, text=True, cwd=str(cwd))  # noqa: S603
		lines = out.stdout.split()
		got = out.stdout.strip()
		ok = all(token in out.stdout for token in expected)
		print(f'[{"PASS" if ok else "FAIL"}] {name}')
		if not ok:
			print(f'    arg={arg} init={init} cwd={cwd_rel}')
			print(f'    expected all of: {expected}')
			print(f'    got stdout: {got!r}')
			if out.stderr.strip():
				print(f'    stderr: {out.stderr.strip()!r}')
		return ok


CASES = [
	# root=None (run_fix_import): namespace pkgs -> single-level `from .` works, `from ..` is beyond top-level
	('root=None, namespace', 'None', False, None, ["PKG 'b'", 'OK from . import x', 'ERR from .. import y']),
	# root=None: __init__.py markers let auto-detect climb to the real package root -> multi-level works
	('root=None, __init__.py', 'None', True, None, ["PKG 'src.a.b'", 'OK from . import x', 'OK from .. import y']),
	# root by bare ancestor name
	("root='src' (name)", "'src'", False, None, ["PKG 'src.a.b'", 'OK from . import x', 'OK from .. import y']),
	# root by leading-dot path, resolved against the file even from an unrelated cwd
	("root='..' (path), other cwd", "'..'", False, '..', ["PKG 'a.b'", 'OK from . import x', 'OK from .. import y']),
	# relative slashed path is resolved against the file; not an ancestor -> clear ImportError (was a crash)
	("root='src/a' (bad rel path)", "'src/a'", False, None, ['RAISE ImportError']),
	# unknown ancestor name -> clear ImportError (was a silent print + None)
	("root='nope' (bad name)", "'nope'", False, None, ['RAISE ImportError']),
]


def main():
	results = [run_case(*c[:-1], c[-1]) for c in CASES]
	total, passed = len(results), sum(results)
	print(f'\n{passed}/{total} passed')
	if passed != total:
		sys.exit(1)


if __name__ == '__main__':
	main()
