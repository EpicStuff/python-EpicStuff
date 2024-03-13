from epicstuff import Dict
from box import Box

print('starting')

x = Dict({'a': 1, 'b': {'c': [3, dict()]}}, _convert=False)

print(x.b)

x.__contains__('a')

'a' in x

print(len(x))

print(x.copy())

x.t = 1

x._w = 2

print(x._w)

print(*[x for x in x])

x['f'] = 'g'

print(x['f'])

print(x == 3)

print(x | {'a': 2, 'e': 999})
print({'a': 2, 'e': 999} | x)

print(reversed(x))

class child(Dict):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)

# z = Dict()

# y.y = 6

# print(y.y)
# print(y)
# print('---')
# print(y.w)
