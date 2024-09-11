from epicstuff import Dict

print('starting')

x = Dict({'a': 1, 'b': {'c': [3, {}]}}, _convert=False)

assert x.b == {'c': [3, {}]}

assert 'a' in x

assert len(x) == 2

assert x.copy() is not x

x.t = 1

x._w = 2

assert x._w == 2

assert [x for x in x] == ['a', 'b', 't']

x['f'] = 'g'

assert x['f'] == 'g'

assert (x == 3) == False

print(x | {'a': 2, 'e': 999})
print({'a': 2, 'e': 999} | x)

print(reversed(x))

class child(Dict):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)
