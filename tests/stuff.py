from epicstuff import Dict, rmap, timer, install_trace, stdtee

install_trace(file=stdtee('output.log'))

d = Dict({"a:a": 1, "b:b": [{"c": 2, "d": 3}, 'd']}, _convert=None)  # ignore the unexpected-keyword-arg warning

def tmp1(key: str):
	if ':' in key:
		parts = key.split(':')
		print('dropping', parts[0], 'from', key)
		return parts[1]
	return key

def tmp2(val: str):
	print('processing', val)
	return '.' + str(val)


assert rmap(d, tmp1, tmp2) == Dict({'a': '.1', 'b': [Dict({'c': '.2', 'd': '.3'}), '.d']})

a = 3

count = 0
with timer():
	for _ in range(1000000):
		try:
			a.x
		except AttributeError:
			count += 1
count = 0
with timer():
	for _ in range(1000000):
		if not hasattr(a, 'x'):
			count += 1

count = 0
with timer():
	for _ in range(1000000):
		try:
			a.__bool__
		except AttributeError:
			count += 1
count = 0
with timer():
	for _ in range(1000000):
		if not hasattr(a, '__bool__'):
			count += 1
