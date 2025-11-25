# ruff: noqa: S101

from epicstuff import Dict, run_install_trace

print('starting')

convert = None
x = Dict(dict([('a', 1), ('b', 2), ('c', 3)], l={'a': 1, 'b': {'c': [3, {}]}}), _convert=convert)

assert x.b == 2

assert 'a' in x

print('len:', len(x))
assert len(x) == 4

assert x.copy() is not x

x.t = 1

x._w = 2

assert x._w == 2

print(x)

# assert [x for x in x] == ['a', 'b', 't']  # not sure how i want to treat attributes that start with
assert [x for x in x] == ['a', 'b', 'c', 'l', 't', '_w']

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

# z = Dict()

# y.y = 6

# print(y.y)
# print(y)
# print('---')
# print(y.w)

class special_dict(dict):
	pass


d = Dict(special_dict(), _convert=False)
print(type(d.data))
print(d.data)
print(d)


print(*x)
print(x._protected_keys)
x._protected_keys.remove('_convert')


x = Dict({'a': 1, 'b': {'a': 1, 'b': 2}}, _convert=False)
x.update(Dict({'b': {'c': 3}}, _convert=False))
print(x)
print(isinstance(x.b, Dict))
assert not isinstance(x.b, Dict)

assert all((isinstance(Dict(), Dict), isinstance(Dict(_convert=False), Dict)))
