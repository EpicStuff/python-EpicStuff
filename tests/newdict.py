# pylint: skip-file
import pickle
from collections import UserDict, abc

from epicstuff import NewDict as Dict, run_install_trace

print('starting')

# =============================================================================
# 1. Construction with nested Dict in source doesn't recurse during repr.
#    Regression check: printing a Dict that holds another Dict shouldn't infloop.
# =============================================================================
print(Dict({'a': {'x': 1, 'y': 2, 'z': 3}, 'b': Dict({'m': 4, 'n': 5, 'o': 6}, _convert=True, _create=True)}))
print('print recursion test passed')

# =============================================================================
# 2. Common dict-like operations across all _convert modes (None / True / False).
#    Exercises:
#      - construction from list-of-tuples + kwargs, and from dict + kwargs
#      - equality with plain dict
#      - dot-read of existing keys
#      - 'in' operator
#      - len(), copy() returns a new instance
#      - dot-write (__setattr__ routes to __setitem__) for both normal and _-prefixed names
#      - iteration order includes dot-set keys
#      - bracket get/set
#      - equality vs non-mapping
#      - | with plain dict (wrap result if _convert is not False, else plain dict)
#      - dict() conversion + reversed()
# =============================================================================
for convert in (None, True, False):
	if convert is False:
		x = Dict(dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}), _convert=False)
	else:
		x = Dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}, _convert=convert)

	assert x == dict(x)

	assert x.b == 2
	assert 'a' in x

	assert len(x) == 3
	assert x.copy() is not x

	x.t = 1
	x._w = 2
	assert x._w == 2

	assert [x for x in x] == ['a', 'b', 'l', 't', '_w']

	x['f'] = 'g'

	assert x['f'] == 'g'
	assert (x == 3) is False

	if convert is False:
		# _convert=False → | returns a plain dict, no dot access on result
		assert type(x | {'a': 999}) is dict
		assert (x | {'a': 999})['a'] == 999

		assert type({'a': 999} | x) is dict
		assert ({'a': 999} | x)['a'] == 1
	else:
		# _convert=None or True → | wraps result, dot access works
		assert (x | {'a': 999}).a == 999

		assert ({'a': 999} | x).a == 1

	dict(x)

	assert list(reversed(x)) == list(reversed(dict(x)))


# =============================================================================
# 3. Subclassing Dict directly.
#    - `protected_attrs={'test'}` extends the protected set on the subclass
#    - subclass __init__ runs after Dict.__init__ via normal MRO
#    - resulting instances are still dict + Dict
# =============================================================================
class child(Dict, protected_attrs={'test'}):
	def __init__(self, *args, **kwargs) -> None:
		print('initing')
		self.x = 3


y = child(w=5)
assert isinstance(y, dict)
assert isinstance(y, Dict)
assert 'test' in y._protected_attrs


# =============================================================================
# 4. Wrapping an arbitrary dict subclass with _convert=False.
#    Exercises the class-swap path in __new__ (source class gets mixed with Dict).
# =============================================================================
class special_dict(dict):
	pass


d = Dict(special_dict(), _convert=False)
print(type(d))
print(d)


print(*x)
print(x._protected_attrs)


# # this test was changed, might not test the orginal intent
# x = Dict({'a': 1, 'b': {'a': 1, 'b': 2}}, _convert=False)
# x.update(Dict({'b': {'c': 3}}, _convert=False))
# # print(x)
# assert x._convert is None


# =============================================================================
# 5. _convert flag is stored as-passed (no auto-promotion of None to True/False).
#    - explicit False stays False
#    - default (omitted) is None
#    - explicit True stays True
#    - explicit None stays None
# =============================================================================
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


# =============================================================================
# 6. _convert=None lazy conversion is one level deep.
#    Accessing d.a wraps the top-level nested mapping, but its internal nested
#    mappings are NOT recursively converted at access time — they only get
#    wrapped when accessed individually.
# =============================================================================
d = Dict({'a': {'b': {'c': 1}}})
assert type(d.a) is Dict
assert type(dict.__getitem__(d.a, 'b')) is not Dict

# =============================================================================
# 7. Getting a nested plain-dict value from a Dot-subclass returns plain NewDict
#    (not another dotSubclass), because nested plain dicts have no source-class
#    behavior to preserve.
# =============================================================================
class tmp(dict): ...
a = Dict(tmp({'a': {'b': 1}}))
assert type(a.a) is Dict

# =============================================================================
# 8. _promote handles class-swap targets in copy().
#    Wrapping a dict-subclass-of-dict-subclass and copying shouldn't crash.
# =============================================================================
class tmp(dict): ...
a = Dict(tmp(tmp({'a': 1})))
a.copy()

# =============================================================================
# 9. Multiple-inheritance subclasses and UserDict variant.
#    - Dict + dict + arbitrary class all work as bases
#    - _warn override is accepted
#    - UserDict subclass is constructible (used in pickle loop below)
# =============================================================================
class test: ...
class y(Dict, dict, test): ...
class test2(Dict):
	def _warn(): ...
class m(UserDict): ...


assert all((isinstance(y(), Dict), isinstance(y(), dict), isinstance(y(), test)))

# =============================================================================
# 10. Pickle round-trip preserves data + flags across a variety of constructions.
#     Note: tmpcreate takes a key arg because __missing__ now calls _create(key).
# =============================================================================
def tmpcreate(key):
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

# =============================================================================
# 11. | operator merges; right operand overrides left on key collisions.
#     Includes |= (in-place merge) for both _convert=None and _convert=False.
# =============================================================================
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

# =============================================================================
# 12. builtin hasattr() on a missing key doesn't raise (returns False).
#     Note: under _create=True the builtin hasattr WILL autovivify (gotcha
#     documented in "21. 'in' is side-effect-free" below).
# =============================================================================
x = Dict({'a': 1, 'b': 2})
hasattr(x, 'nonexistent_attribute')  # should not raise

# =============================================================================
# 13. | left-vs-right precedence on overlapping keys.
#     a | b → b wins; b | a → a wins (matches stdlib dict semantics).
# =============================================================================
a = Dict(a=1)
b = Dict(a = 2)
assert (a | b).a == 2
assert (b | a).a == 1

# =============================================================================
# 14. Empty Dict is a real dict (isinstance(dict)) and a Mapping.
#     This is the property NewDict gained over old JDict.
# =============================================================================
x = Dict()
assert (isinstance(x, Dict), isinstance(x, dict), isinstance(x, abc.Mapping)) == (True, True, True)

# =============================================================================
# 15. .values() yields unpackable values.
# =============================================================================
a, b = Dict({'a': {}, 'b': {}}).values()

# =============================================================================
# 16. Wrapping a Dict in Dict (with _convert=False) — sanity check, no crash.
# =============================================================================
# assert Dict(Dict(_create=True), _convert=None)._create is not False
Dict(Dict(_convert=False), _convert=False)

# =============================================================================
# 17. _convert=None: mutations through dot-accessed nested mappings propagate.
#     This works because the lazy convert caches the wrapper in parent storage
#     on first access (convert-and-cache).
#     Documented limitation: dicts inside lists are NOT wrapped, so mutating
#     them through dot-access only works because the raw list is returned.
# =============================================================================
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


# =============================================================================
# 18. _create=True uses the class-level default factory (returns a fresh Dict).
#     Chained autovivify: d.a.b.c = 1 should build the intermediate dicts.
# =============================================================================
d = Dict(_create=True)
d.a.b.c = 1
assert d.a.b.c == 1
assert type(d.a) is Dict

# =============================================================================
# 19. _create with a custom callable. The callable receives the missing key
#     (signature: _create(key) -> value).
# =============================================================================
def custom_factory(key):
	return f'default-{key}'

d = Dict(_create=custom_factory)
assert d.missing == 'default-missing'
assert d['other'] == 'default-other'
# autovivify persisted the values
assert 'missing' in d and 'other' in d

# =============================================================================
# 20. __missing__ raises KeyError when _create is False.
#     Direct bracket access on missing key should KeyError;
#     dot-access on missing should become AttributeError.
# =============================================================================
d = Dict({'a': 1})
try:
	_ = d['nonexistent']
	raise AssertionError('expected KeyError')
except KeyError:
	pass
try:
	_ = d.nonexistent
	raise AssertionError('expected AttributeError')
except AttributeError:
	pass

# =============================================================================
# 21. 'in' is side-effect-free, even with _create=True.
#     This is the recommended way to check key existence on a Dict.
#     (Builtin hasattr() under _create=True DOES autovivify — see 22.)
# =============================================================================
d = Dict(_create=True)
assert 'nope' not in d
assert 'nope' not in d  # second check confirms no creation occurred
assert len(d) == 0

# =============================================================================
# 22. The instance .hasattr / .getattr methods suppress _create.
#     Provided for users who want hasattr-style checks without autovivify.
# =============================================================================
d = Dict(_create=True)
assert d.hasattr('nope') is False
assert len(d) == 0  # no side effect
assert d.getattr('nope', 'default') == 'default'
assert len(d) == 0  # no side effect

# Existence cases for hasattr/getattr
d = Dict({'a': 1})
assert d.hasattr('a') is True
assert d.getattr('a') == 1
assert d.getattr('missing', 'fallback') == 'fallback'

# =============================================================================
# 23. del d.foo and del d['foo'] both remove the key.
#     Deleting a missing attribute raises AttributeError;
#     deleting a missing key raises KeyError.
# =============================================================================
d = Dict({'a': 1, 'b': 2})
del d.a
assert 'a' not in d
assert d.b == 2
try:
	del d.nonexistent
	raise AssertionError('expected AttributeError')
except AttributeError:
	pass
try:
	del d['also_nonexistent']
	raise AssertionError('expected KeyError')
except KeyError:
	pass

# =============================================================================
# 24. copy.copy and copy.deepcopy produce independent Dict instances.
#     Deepcopy yields full deep independence on nested mutable values.
# =============================================================================
import copy as _copy

d = Dict({'a': 1, 'b': {'nested': [1, 2, 3]}}, _convert=True)
c = _copy.copy(d)
assert c == d and c is not d
assert isinstance(c, Dict)

dd = _copy.deepcopy(d)
assert dd == d and dd is not d
dd.b.nested.append(4)
assert d.b.nested == [1, 2, 3]  # original untouched

# =============================================================================
# 25. update() with _convert=True converts nested mappings on insert.
#     (With _convert=False/None, update bypasses conversion — see code.)
# =============================================================================
d = Dict(_convert=True)
d.update({'a': {'b': 1}, 'c': [{'nested': 2}]})
assert type(d.a) is Dict          # nested dict converted on insert
assert d.a.b == 1
assert isinstance(d.c, list)       # list preserved
assert type(d.c[0]) is Dict        # dict inside list converted

# =============================================================================
# 26. _convert=None convert-and-cache: lazy conversion caches the wrapper in
#     parent storage on first access. Implementation-detail check, but it's
#     the mechanism that makes the mutation-propagation test in §17 pass.
# =============================================================================
d = Dict({'a': {'b': 1}}, _convert=None)
assert type(dict.__getitem__(d, 'a')) is dict   # before access: raw dict
_ = d.a                                          # trigger lazy convert
assert type(dict.__getitem__(d, 'a')) is Dict   # after access: cached as Dict

# =============================================================================
# 27. Wrapping a Dict (_convert=False) inside another Dict (_convert=False)
#     should not double-wrap; should be a no-op at the class level.
# =============================================================================
inner = Dict({'x': 1}, _convert=False)
outer = Dict(inner, _convert=False)
assert outer is inner or outer == inner  # same instance or equivalent
assert outer._convert is False

# =============================================================================
# 28. dict.get on a Dict with _create=True does NOT autovivify (since get is
#     C-level on dict and doesn't go through __getitem__/__missing__).
# =============================================================================
d = Dict(_create=True)
assert d.get('nope') is None
assert d.get('nope', 'fallback') == 'fallback'
assert 'nope' not in d  # confirmed no side effect

# =============================================================================
# 29. CommentedMap source — comments preserved when ruamel.yaml is installed.
#     Skipped silently otherwise.
# =============================================================================
try:
	from ruamel.yaml.comments import CommentedMap
	cm = CommentedMap({'a': 1, 'b': 2})
	cm.yaml_set_comment_before_after_key('a', before='hello')
	d = Dict(cm)
	assert d.a == 1
	assert d.b == 2
	# comment machinery still accessible (CommentedMap-specific attribute)
	assert d.ca is not None
	# d is both a CommentedMap and a Dict
	assert isinstance(d, CommentedMap)
	assert isinstance(d, Dict)
except ImportError:
	pass

print('all newdict tests passed (or noted as intended failures)')
