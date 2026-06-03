# pylint: skip-file
import pickle
from collections import UserDict, abc

from epicstuff import NewDict as Dict, run_install_trace

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

	# print(x)

	# assert [x for x in x] == ['a', 'b', 't']  # not sure how i want to treat attributes that start with
	assert [x for x in x] == ['a', 'b', 'l', 't', '_w']

	x['f'] = 'g'

	assert x['f'] == 'g'
	assert (x == 3) is False

	# print(x | {'a': 999})
	# print({'a': 999} | x)
	if convert is False:
		assert type(x | {'a': 999}) is dict
		assert (x | {'a': 999})['a'] == 999
		
		assert type({'a': 999} | x) is dict
		assert ({'a': 999} | x)['a'] == 1
	else:
		assert (x | {'a': 999}).a == 999
	
		assert ({'a': 999} | x).a == 1

	dict(x)

	assert list(reversed(x)) == list(reversed(dict(x)))


class child(Dict, protected_attrs={'test'}):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)
assert isinstance(y, dict)
assert isinstance(y, Dict)
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
print(type(d))
print(d)


print(*x)
print(x._protected_attrs)
# x._protected_attrs.remove('_convert')


# # this test was changed, might not test the orginal intent
# x = Dict({'a': 1, 'b': {'a': 1, 'b': 2}}, _convert=False)
# x.update(Dict({'b': {'c': 3}}, _convert=False))
# # print(x)
# assert x._convert is None


x = Dict({'a': {'b': {'c': 3}}}, _convert=False)
assert x._convert is False
assert isinstance(x, Dict)
x = Dict({'a': {'b': {'c': 3}}})
assert x._convert is None
assert isinstance(x, Dict)
x = Dict({'a': {'b': {'c': 3}}}, _convert=True)
assert x._convert is True
assert isinstance(x, Dict)
x = Dict({'a': {'b': {'c': 3}}}, _convert=None)
assert x._convert is None
assert isinstance(x, Dict)


# check that convert None does 1 level conversion (yes conversion but no recursive conversion)
d = Dict({'a': {'b': {'c': 1}}})
assert type(d.a) is Dict
assert type(dict.__getitem__(d.a, 'b')) is not Dict

# check that getitem convert returns newdict instead of dottmp
class tmp(dict): ...
a = Dict(tmp({'a': {'b': 1}}))
assert type(a.a) is Dict

# check that _promote work
class tmp(dict): ...
a = Dict(tmp(tmp({'a': 1})))
a.copy()

class test: ...
class y(Dict, dict, test): ...
class test2(Dict):
	def _warn(): ...
class m(UserDict): ...
	

assert all((isinstance(y(), Dict), isinstance(y(), dict), isinstance(y(), test)))

def tmpcreate():
	return None

x = [
	Dict({'mobile': 1, 'desktop': 2}, _convert=False),
	Dict({'mobile': 2, 'desktop': 2}, _convert=True),
	Dict({'mobile': 3, 'desktop': 2}),
	Dict({'mobile': 4, 'desktop': 2}, _create=True),
	y({'mobile': 5, 'desktop': 2}, _convert=False),
	m({'mobile': 6, 'desktop': 2}, _create=tmpcreate),
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

a = Dict(a=1)
b = Dict(a = 2)
assert (a | b).a == 2
assert (b | a).a == 1 

x = Dict()
assert (isinstance(x, Dict), isinstance(x, dict), isinstance(x, abc.Mapping)) == (True, True, True)

a, b = Dict({'a': {}, 'b': {}}).values()

# assert Dict(Dict(_create=True), _convert=None)._create is not False
Dict(Dict(_convert=False), _convert=False)

# check that when convert is None, changes to returned dict from getitem gets reflected in original
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