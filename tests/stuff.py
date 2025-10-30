from epicstuff import Dict, rmap

d = Dict({"a:a": 1, "b:b": [{"c": 2, "d": 3}, 'd']})  # ignore the unexpected-keyword-arg warning

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
