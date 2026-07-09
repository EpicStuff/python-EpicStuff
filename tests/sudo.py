import os, unittest

from epicstuff import NewDict as Dict, sudo
from rich.traceback import install

# under a test runner (green), sudo()'s subprocess inherits the real fd 1 and bypasses
# the runner's sys.stdout capture; drop that fd to devnull so its output stays quiet
_UNDER_RUNNER = __name__ != '__main__'


def is_root() -> bool:
	return os.getuid() == 0


def complex_object(arg) -> Dict:
	return Dict(a=1)


def func_with_print():
	print('test')


class TestSudo(unittest.TestCase):
	_saved_fd: int = -1

	def setUp(self):
		if _UNDER_RUNNER:
			self._saved_fd = os.dup(1)
			devnull = os.open(os.devnull, os.O_WRONLY)
			os.dup2(devnull, 1)
			os.close(devnull)

	def tearDown(self):
		if _UNDER_RUNNER:
			os.dup2(self._saved_fd, 1)
			os.close(self._saved_fd)

	def test_sudo_toggles_root(self):
		out = is_root()
		print('no sudo, is root:', out)
		assert not out
		out = sudo(is_root)
		print('during sudo, is root:', out)
		assert out
		out = is_root()
		print('after sudo, is root:', out)
		assert not out

	def test_complex_object(self):
		out = sudo(complex_object, install)
		print('got complex object:', out)
		assert isinstance(out, Dict)

	def test_func_with_print(self):
		sudo(func_with_print)


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(TestSudo).debug()
	print('All tests passed')
