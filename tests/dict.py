# ruff: noqa: S101
import pickle
from epicstuff import BoxDict, Dict, JDict, run_install_trace

print('starting')

for convert in (None, True, False):
	if convert is False:
		x = Dict(dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}), _convert=False)
	else:
		x = Dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}, _convert=convert)

	assert x.b == 2
	assert 'a' in x

	# print('len:', len(x))
	assert len(x) == 3
	assert x.copy() is not x

	x.t = 1
	x._w = 2
	assert x._w == 2

	print(x)

	# assert [x for x in x] == ['a', 'b', 't']  # not sure how i want to treat attributes that start with
	assert [x for x in x] == ['a', 'b', 'l', 't', '_w']

	x['f'] = 'g'

	assert x['f'] == 'g'
	assert (x == 3) is False

	# TODO
	# # print(x | {'a': 999})
	# assert (x | {'a': 2}).a == 999
	# # print({'a': 999} | x)
	# assert ({'a': 999} | x).a == 2

	dict(x)

	if isinstance(x, JDict):
		assert list(reversed(x)) == list(reversed(x.data))
	else:
		assert list(reversed(x)) == list(reversed(dict(x)))


class child(Dict):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)
# print(y)  # TODO

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
# x._protected_keys.remove('_convert')


# this test was changed, might not test the orginal intent
x = Dict({'a': 1, 'b': {'a': 1, 'b': 2}}, _convert=False)
x.update(Dict({'b': {'c': 3}}, _convert=False))
print(x)
assert x._convert is None

assert all((isinstance(Dict(), Dict), isinstance(Dict(_convert=False), Dict)))

x = Dict({'a': {'b': {'c': 3}}}, _convert=False)
assert x._convert is None

x = Dict({'a': {'b': {'c': 3}}})
assert x._convert is None

class y(BoxDict): ...


x = [
	y({'mobile': 1, 'desktop': 2}, _convert=False),
	Dict({'mobile': 1, 'desktop': 2}, _convert=False),
	Dict({'mobile': 1, 'desktop': 2}, _convert=True),
	Dict({'mobile': 1, 'desktop': 2}),
	Dict({'mobile': 1, 'desktop': 2}, _create=True),
]

for d in x:
	with open('test.pkl', 'wb') as f:
		pickle.dump(d, f)
	with open('test.pkl', 'rb') as f:
		data = pickle.load(f)
	print(data, getattr(d, '_create', None))
	assert data == d
