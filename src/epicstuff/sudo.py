import functools, json, subprocess, sys, tempfile
from collections import abc
from pathlib import Path
from typing import Any


def sudo(func: abc.Callable, *args: Any, _prefer_graphical: bool = False, **kwargs: Any) -> Any:
	'''Run a function with elevated privileges.'''
	import cloudpickle, tblib.pickling_support
	tblib.pickling_support.install()

	# run the function
	payload = cloudpickle.dumps(functools.partial(func, *args, **kwargs))

	with tempfile.TemporaryDirectory() as tmpdir:
		result = Path(tmpdir) / 'result.pkl'
		proc = subprocess.run([sys.executable, __file__, str(int(_prefer_graphical)), json.dumps(sys.path), result], input=payload)

		# get and return result
		try:
			with result.open('rb') as f:
				data = f.read()
		except FileNotFoundError:
			data = b''
		if not data:
			raise RuntimeError(f'elevated subprocess exited {proc.returncode} without a result')

	status, value = cloudpickle.loads(data)
	if status == 1:
		raise value
	if status == 2:
		raise SystemExit(value)
	return value


def main() -> None:
	sys.dont_write_bytecode = True

	# add user site-packages to root path and stuff
	sys.path[:] = json.loads(sys.argv[2])
	import cloudpickle, tblib.pickling_support
	from elevate import elevate
	tblib.pickling_support.install()

	# elevate
	has_tty = False
	if sys.argv[1] == '0':
		try:
			with Path('/dev/tty').open('rb+'):
				has_tty = True
		except OSError:
			pass
	elevate(graphical=not has_tty)

	# load the function
	func = cloudpickle.loads(sys.stdin.buffer.read())
	# run the function
	try:
		result = (0, func())
	except SystemExit as e:
		result = (2, e.code)
	except BaseException as e:  # noqa: BLE001  # tblib installed above → traceback survives pickling
		result = (1, e)

	# return result; serialize before opening so a pickling failure leaves no (empty) file
	blob = cloudpickle.dumps(result)
	with Path(sys.argv[3]).open('wb') as f:
		f.write(blob)


if __name__ == '__main__':
	main()
