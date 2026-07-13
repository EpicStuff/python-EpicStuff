import base64, pickle, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path

from parameterized import parameterized
from tblib import pickling_support


# let the child process's exceptions pickle WITH their traceback (via tblib) so a failing case can re-raise
# the child's real traceback in this process, instead of an assertion pointing at the test harness
pickling_support.install()

# Script executed AS the importer module (run directly, so __name__ == '__main__', the exact situation
# fix_import is meant to repair). It emits one-line PKG/OK/ERR/RAISE tokens for assertions, plus an `EXC
# <base64> <step>` line carrying the pickled exception+traceback for any step that raised, so the parent
# can re-raise the child's real traceback. No literal braces here -> it stays a plain .format template.
RUNNER = '''
import base64, pickle, sys, traceback

sys.path[:0] = {syspath!r}
try:
	from tblib import pickling_support
	pickling_support.install()  # so the pickled exception carries its traceback across the process boundary
except ImportError:
	pickling_support = None

from epicstuff import fix_import

def emit(tag, exc):
	if pickling_support is not None:
		print('EXC', base64.b64encode(pickle.dumps(exc)).decode(), tag)

try:
	fix_import({arg})
except Exception as e:
	print('RAISE', type(e).__name__ + ':', e)  # 'RAISE <Type>' still matches as a token prefix
	traceback.print_exc()  # readable stderr copy even if tblib is unavailable
	emit('fix_import', e)
	raise SystemExit
print('PKG', repr(__package__))
for stmt in ['from . import x', 'from .. import y']:
	try:
		exec(stmt)
		print('OK', stmt)
	except Exception as e:
		print('ERR', stmt, type(e).__name__, e)
		emit(stmt, e)
'''


def build_tree(base: Path, init: bool) -> Path:
	'proj/src/a/b/{run.py,x.py} + proj/src/a/y.py, optionally with __init__.py markers.'
	b = base / 'proj' / 'src' / 'a' / 'b'
	b.mkdir(parents=True)
	(b / 'x.py').write_text("VAL = 'x'\n")
	(b.parent / 'y.py').write_text("VAL = 'y'\n")
	if init:
		for d in (base / 'proj' / 'src', base / 'proj' / 'src' / 'a', b):
			(d / '__init__.py').write_text('')
	return b


CASES = [
	# root=None (run_fix_import): namespace pkgs -> single-level `from .` works, `from ..` is beyond top-level
	('root=None, namespace', 'None', False, None, ["PKG 'b'", 'OK from . import x', 'ERR from .. import y']),
	# root=None: __init__.py markers let auto-detect climb to the real package root -> multi-level works
	('root=None, __init__.py', 'None', True, None, ["PKG 'src.a.b'", 'OK from . import x', 'OK from .. import y']),
	# root by bare ancestor name
	("root='src' (name)", "'src'", False, None, ["PKG 'src.a.b'", 'OK from . import x', 'OK from .. import y']),
	# root by leading-dot path, resolved against the file even from an unrelated cwd
	("root='..' (path), other cwd", "'..'", False, '..', ["PKG 'a.b'", 'OK from . import x', 'OK from .. import y']),
	# relative='cwd': the path resolves against cwd (proj), not the file -> valid even though './src' is not by the file
	("root='./src' (path), relative='cwd'", "'./src', relative='cwd'", False, 'proj', ["PKG 'src.a.b'", 'OK from . import x', 'OK from .. import y']),
	# relative slashed path is resolved against the file; not an ancestor -> clear ImportError (was a crash)
	("root='src/a' (bad rel path)", "'src/a'", False, None, ['RAISE ImportError']),
	# unknown ancestor name -> clear ImportError (was a silent print + None)
	("root='nope' (bad name)", "'nope'", False, None, ['RAISE ImportError']),
]


class TestFixImport(unittest.TestCase):
	@parameterized.expand(CASES)
	def test_fix_import(self, name, arg, init, cwd_rel, expected) -> None:
		'Build a fresh tree, run the importer script as a subprocess, assert on its output lines.'
		with tempfile.TemporaryDirectory() as tmp:
			base = Path(tmp)
			b = build_tree(base, init)
			run_py = b / 'run.py'
			run_py.write_text(RUNNER.format(syspath=sys.path, arg=arg))
			cwd = base if cwd_rel is None else base / cwd_rel
			out = subprocess.run([sys.executable, str(run_py)], capture_output=True, text=True, cwd=str(cwd))  # noqa: S603
			# peel the child's `EXC <base64> <step>` lines (pickled exception+traceback) off the visible output
			captured, visible = {}, []
			for line in out.stdout.splitlines():
				if line.startswith('EXC '):
					_, blob, tag = line.split(' ', 2)
					captured[tag] = pickle.loads(base64.b64decode(blob))
				else:
					visible.append(line)
			visible = '\n'.join(visible)
			missing = [token for token in expected if token not in visible]
			if missing:
				# the child exception behind the first missing `OK <stmt>`, else an unexpected fix_import crash
				culprit = next((captured[t[3:]] for t in missing if t.startswith('OK ') and t[3:] in captured), None) or captured.get('fix_import')
				# self.failureException (not assertFalse) so the message stands alone — no '[…] is not false'
				# prefix — and the child's real stdout/stderr are inline instead of 'see output above'
				detail = '\n'.join([
					f'{name}: fix_import({arg}) did not produce the expected output   (init={init}, cwd={cwd_rel})',
					f'  missing tokens : {missing}',
					f'  expected all of: {expected}',
					'  ------ actual stdout ------',
					textwrap.indent(visible.strip() or '(empty)', '  '),
					'  ------ actual stderr ------',
					textwrap.indent(out.stderr.strip() or '(empty)', '  '),
				])
				# re-raise the child's REAL traceback first (`from culprit`), then this summary; fall back to a
				# plain fail when the child never raised (e.g. it printed the wrong __package__ and exited 0)
				if culprit is not None:
					raise self.failureException(detail) from culprit
				self.fail(detail)


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(TestFixImport).debug()
	print('All tests passed')
