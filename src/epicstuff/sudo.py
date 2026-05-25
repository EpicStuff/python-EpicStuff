import functools, pickle, site, subprocess, sys
from collections import abc
from pathlib import Path
from typing import Any


def sudo(func: abc.Callable, *args: Any, _prefer_graphical: bool = False, **kwargs: Any) -> Any:
	'''Run a function with elevated privileges.'''
	import cloudpickle, tblib.pickling_support
	tblib.pickling_support.install()

	# run the function
	payload = cloudpickle.dumps((sys.path, functools.partial(func, *args, **kwargs)))
	proc = subprocess.run([sys.executable, __file__, str(int(_prefer_graphical)), site.getusersitepackages()], input=payload, capture_output=True)

	# get and return result
	try:
		status, value = pickle.loads(proc.stdout)
	except Exception as e:
		raise RuntimeError(
			f'sudo subprocess exited {proc.returncode} without a result:\n'
			f'{proc.stderr.decode(errors="replace")}',
		) from e
	if status == 1:
		raise value
	if status == 2:
		raise SystemExit(value)
	return value


def main() -> None:
	sys.dont_write_bytecode = True

	# add user site-packages to root path and stuff
	site.addsitedir(sys.argv[2])
	import tblib.pickling_support
	from elevate import elevate
	tblib.pickling_support.install()

	# elevate
	has_tty = False
	try:
		with Path('/dev/tty').open('rb+'):
			has_tty = True
	except OSError:
		pass
	elevate(graphical=not has_tty)

	# load the function
	import cloudpickle
	parent_path, func = cloudpickle.loads(sys.stdin.buffer.read())
	for p in parent_path:
		site.addsitedir(p)
	# run the function
	try:
		result = (0, func())
	except Exception as e:
		result = (1, e)
	except SystemExit as e:
		result = (2, e.code)

	# return result
	sys.stdout.buffer.write(pickle.dumps(result))


if __name__ == '__main__':
	main()
