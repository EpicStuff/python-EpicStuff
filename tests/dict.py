import pickle
# pylint: skip-file
from collections import abc

from epicstuff import BoxDict, Dict, JDict, run_install_trace

print('starting')

print(Dict({'a': {'x': 1, 'y': 2, 'z': 3}, 'b': Dict({'m': 4, 'n': 5, 'o': 6}, _convert=True, _create=True)}))
print('print recursion test passed')

for convert in (None, True, False):
	if convert is False:
		x = Dict(dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}), _convert=False)
	else:
		x = Dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}, _convert=convert)

	assert x == dict(x)

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

	# print(x | {'a': 999})
	assert (x | {'a': 999}).a == 999
	# print({'a': 999} | x)
	assert ({'a': 999} | x).a == 1

	dict(x)

	if isinstance(x, JDict):
		assert list(reversed(x)) == list(reversed(x._t))
	else:
		assert list(reversed(x)) == list(reversed(dict(x)))


class child(Dict, protected_attrs={'test'}):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)
assert isinstance(y, Dict)
assert isinstance(y, BoxDict)
assert 'test' in y._protected_attrs

# z = Dict()

# y.y = 6

# print(y.y)
# print(y)
# print('---')
# print(y.w)

class special_dict(dict):
	pass


d = Dict(special_dict(), _convert=False)
print(type(d._t))
print(d._t)
print(d)


print(*x)
print(x._protected_attrs)
# x._protected_attrs.remove('_convert')


# this test was changed, might not test the orginal intent
x = Dict({'a': 1, 'b': {'a': 1, 'b': 2}}, _convert=False)
x.update(Dict({'b': {'c': 3}}, _convert=False))
print(x)
assert x._convert is None

assert all((isinstance(Dict(), Dict), isinstance(Dict(_convert=False), Dict)))

x = Dict({'a': {'b': {'c': 3}}}, _convert=False)
assert x._convert is None
assert isinstance(x, JDict)
x = Dict({'a': {'b': {'c': 3}}})
assert x._convert is None
assert isinstance(x, JDict)
x = Dict({'a': {'b': {'c': 3}}}, _convert=True)
assert x._convert is True
assert isinstance(x, BoxDict)
x = Dict({'a': {'b': {'c': 3}}}, _convert=None)
assert x._convert is None
assert isinstance(x, BoxDict)


class test: ...
class y(Dict, dict, test): ...
class test2(Dict):
	def _warn(): ...


assert all((isinstance(y(), BoxDict), isinstance(y(), dict), isinstance(y(), test)))

x = [
	Dict({'mobile': 1, 'desktop': 2}, _convert=False),
	Dict({'mobile': 1, 'desktop': 2}, _convert=True),
	Dict({'mobile': 1, 'desktop': 2}),
	Dict({'mobile': 1, 'desktop': 2}, _create=True),
	y({'mobile': 1, 'desktop': 2}, _convert=False),
]

for d in x:
	with open('test.pkl', 'wb') as f:
		pickle.dump(d, f)
	with open('test.pkl', 'rb') as f:
		data = pickle.load(f)
	print(data, getattr(d, '_create', None))
	assert data == d

x = Dict({'a': 1, 'b': 2})
assert (x | {'b': 3}) == Dict({'a': 1, 'b': 3})
assert ({'b': 3} | x) == Dict({'a': 1, 'b': 2})
x |= {'b': 4}
assert x == Dict({'a': 1, 'b': 4})

x = Dict({'a': 1, 'b': 2}, _convert=False)
assert (x | {'b': 3}) == Dict({'a': 1, 'b': 3}, _convert=False)
assert ({'b': 3} | x) == Dict({'a': 1, 'b': 2}, _convert=False)
x |= {'b': 4}
assert x == Dict({'a': 1, 'b': 4}, _convert=False)

x = Dict({'a': 1, 'b': 2})
hasattr(x, 'nonexistent_attribute')  # should not raise

x = Dict()
assert (isinstance(x, Dict), isinstance(x, dict), isinstance(x, abc.Mapping)) == (True, False, True)

a, b = Dict({'a': {}, 'b': {}}).values()

# assert Dict(Dict(_create=True), _convert=None)._create is not False
Dict(Dict(_convert=False), _convert=False)

x = Dict(_convert=None)
x.a = {}
x.a['b'] = 1
assert x.a['b'] == 1

x = Dict(_convert=None)
x.a = [{}, {}, {}]
x.a[1]['b'] = 1
assert x.a[1]['b'] == 1

# TODO: sort out how _convert/_create should behave on recreation, and if it should propagate to children on change
# # make sure that convert/create gets set on "recreation"
# x = Dict(_convert=None)
# assert Dict(x, _convert=True)._convert is True
# x = Dict(_create=True)
# assert Dict(x)._create is False
# # make sure that convert gets passed down
# assert Dict(a=Dict(), b=3, _convert=True).a._convert is True
