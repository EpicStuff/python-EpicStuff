import unittest

from epicstuff import NewDict as Dict, rmap


def tmp1(key: str):
	if ':' in key:
		parts = key.split(':')
		print('dropping', parts[0], 'from', key)
		return parts[1]
	return key

def tmp2(val: str):
	print('processing', val)
	return '.' + str(val)

class Main(unittest.TestCase):
	def test_rmap(self) -> None:
		d = Dict({'a:a': 1, 'b:b': [{'c': 2, 'd': 3}, 'd']}, _convert=None)  # ignore the unexpected-keyword-arg warning
		assert rmap(d, tmp2, tmp1) == Dict({'a': '.1', 'b': [Dict({'c': '.2', 'd': '.3'}), '.d']})


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(Main).debug()
	print('All tests passed')
