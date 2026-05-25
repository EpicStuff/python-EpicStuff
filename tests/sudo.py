import os
from sudo import sudo
from epicstuff import Dict
from rich.traceback import install

def is_root() -> bool:
	return os.getuid() == 0


out = is_root()
print('no sudo, is root:', out)
assert not out
out = sudo(is_root)
print('during sudo, is root:', out)
assert out
out = is_root()
print('after sudo, is root:', out)
assert not out

def complex_object(arg) -> Dict:
	return Dict(a=1)


out = sudo(complex_object, install)
print('got complex object:', out)
assert isinstance(out, Dict)

def func_with_print():
	print('test')


sudo(func_with_print)
