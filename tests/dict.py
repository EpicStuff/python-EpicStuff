from epicstuff import Dict
from box import Box

x = Dict({'a': 1, 'b': {'c': 2, 'd': [3, [[dict(), 3], {'a': dict()}, dict()], {'e': 5}]}}, _convert=False)

print(x.b)


class child(Dict):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)

y.y = 6

print(y.y)
print(y.w)
