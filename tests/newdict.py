# pylint: skip-file
import copy as _copy, os, pickle
from collections import abc

from epicstuff import NewDict as Dict, run_install_trace
from epicstuff.dict import Copy

print('starting')


# =============================================================================
# Harness: every test is a function. By default each runs in isolation and
# reports PASS/FAIL so all failures surface in one run; with stop_on_fail the
# first failure propagates so a debugger halts at it.
# =============================================================================
def _run(tests, stop_on_fail=True):
	failed = []
	for name, fn in tests:
		if stop_on_fail:
			print(f'  ...  {name}')
			fn()  # let it raise -> debugger / VSCode stops at the failing line
			print(f'  PASS: {name}')
			continue
		try:
			fn()
			print(f'  PASS: {name}')
		except Exception as e:
			failed.append(name)
			print(f'  FAIL: {name}: {type(e).__name__}: {e}')
	return failed


# --- module-level classes that must be picklable (resolved by qualified name) -
class test: ...
class y(Dict, dict, test): ...
class _Special(dict): pass


# =============================================================================
# 1. Construction with nested Dict in source doesn't recurse during repr.
# =============================================================================
def test_01_print_no_recursion():
	print(Dict({'a': {'x': 1, 'y': 2, 'z': 3}, 'b': Dict({'m': 4, 'n': 5, 'o': 6}, _convert=True, _create=True)}))


# =============================================================================
# 2. Common dict-like operations across all _convert modes (None / True / False).
#    Construction from list-of-tuples/dict + kwargs, equality, dot read/write,
#    'in', len, copy, iteration order, bracket get/set, | with plain dict,
#    dict() + reversed().
# =============================================================================
def test_02_dict_ops_all_convert_modes():
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

		assert [k for k in x] == ['a', 'b', 'l', 't', '_w']

		x['f'] = 'g'

		assert x['f'] == 'g'
		assert (x == 3) is False

		# | always returns a NewDict subclass carrying x's settings (never a bare
		# dict), in every _convert mode; other's keys win in x|other, x's in other|x
		assert type(x | {'a': 999}) is Dict
		assert (x | {'a': 999}).a == 999

		assert type({'a': 999} | x) is Dict
		assert ({'a': 999} | x).a == 1

		dict(x)

		assert list(reversed(x)) == list(reversed(dict(x)))

	# (was the orphan prints after §4, using the last-iteration x)
	print(*x)
	print(x._protected_attrs)


# =============================================================================
# 3. Subclassing Dict directly.
#    - protected_attrs={'test'} extends the protected set on the subclass
#    - subclass __init__ calls super().__init__ (so NewDict's init actually runs)
#    - resulting instances are still dict + Dict
# =============================================================================
def test_03_subclassing():
	class child(Dict, protected_attrs={'test'}):
		def __init__(self, *args, **kwargs) -> None:
			print('initing')
			super().__init__(*args, **kwargs)
			self.x = 3

	c = child(w=5)
	assert isinstance(c, dict)
	assert isinstance(c, Dict)
	assert 'test' in c._protected_attrs


# =============================================================================
# 5. _convert flag is stored as-passed (no auto-promotion).
# =============================================================================
def test_05_convert_flag_stored_as_passed():
	x = Dict({'a': {'b': {'c': 3}}}, _convert=False)
	assert x._s.convert is False
	assert isinstance(x, Dict)
	x = Dict({'a': {'b': {'c': 3}}})
	assert x._s.convert is None
	assert isinstance(x, Dict)
	x = Dict({'a': {'b': {'c': 3}}}, _convert=True)
	assert x._s.convert is True
	assert isinstance(x, Dict)
	x = Dict({'a': {'b': {'c': 3}}}, _convert=None)
	assert x._s.convert is None
	assert isinstance(x, Dict)


# =============================================================================
# 6. _convert=None lazy conversion is one level deep.
# =============================================================================
def test_06_lazy_convert_one_level():
	d = Dict({'a': {'b': {'c': 1}}})
	assert type(d.a) is Dict
	assert type(dict.__getitem__(d.a, 'b')) is not Dict


# =============================================================================
# 7. Nested plain-dict value from a Dot-subclass returns plain NewDict.
# =============================================================================
def test_07_nested_plain_dict_is_newdict():
	class tmp(dict): ...
	a = Dict(tmp({'a': {'b': 1}}))
	assert type(a.a) is Dict


# =============================================================================
# 9. Multiple-inheritance subclass is still a Dict, a dict, and the mixed-in base.
# =============================================================================
def test_09_multiple_inheritance():
	assert all((isinstance(y(), Dict), isinstance(y(), dict), isinstance(y(), test)))


# =============================================================================
# 10. Pickle round-trip preserves data + flags across a variety of constructions.
# =============================================================================
def test_10_pickle_roundtrip():
	x = [
		Dict({'mobile': 1, 'desktop': 2}, _convert=False),
		Dict({'mobile': 2, 'desktop': 2}, _convert=True),
		Dict({'mobile': 3, 'desktop': 2}),
		Dict({'mobile': 4, 'desktop': 2}, _create=True),
		y({'mobile': 5, 'desktop': 2}, _convert=False),
	]

	for d in x:
		with open('test.pkl', 'wb') as f:
			pickle.dump(d, f)
		with open('test.pkl', 'rb') as f:
			data = pickle.load(f)
		print(data, d._s.create)
		assert data == d


# =============================================================================
# 11. | merges; right operand overrides left. Includes |= for None and False.
# =============================================================================
def test_11_or_merge():
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
# 12. builtin hasattr() on a missing key doesn't raise.
# =============================================================================
def test_12_hasattr_missing():
	x = Dict({'a': 1, 'b': 2})
	hasattr(x, 'nonexistent_attribute')  # should not raise


# =============================================================================
# 13. | left-vs-right precedence on overlapping keys.
# =============================================================================
def test_13_or_precedence():
	a = Dict(a=1)
	b = Dict(a=2)
	assert (a | b).a == 2
	assert (b | a).a == 1


# =============================================================================
# 14. Empty Dict is a real dict and a Mapping.
# =============================================================================
def test_14_empty_is_dict_and_mapping():
	x = Dict()
	assert (isinstance(x, Dict), isinstance(x, dict), isinstance(x, abc.Mapping)) == (True, True, True)


# =============================================================================
# 15. .values() yields unpackable values.
# =============================================================================
def test_15_values_unpackable():
	a, b = Dict({'a': {}, 'b': {}}).values()


# =============================================================================
# 17. _convert=None: mutations through dot-accessed nested mappings propagate.
# =============================================================================
def test_17_mutation_propagation():
	x = Dict(_convert=None)
	x.a = {}
	x.a['b'] = 1
	assert x.a['b'] == 1

	x = Dict(_convert=None)
	x.a = [{}, {}, {}]
	x.a[1]['b'] = 1
	assert x.a[1]['b'] == 1


# =============================================================================
# 18. _create=True uses the class-level default factory. Chained autovivify.
# =============================================================================
def test_18_create_true_autovivify():
	d = Dict(_create=True)
	d.a.b.c = 1
	assert d.a.b.c == 1
	assert type(d.a) is Dict


# =============================================================================
# 19. _create with a custom callable; the callable receives the missing key.
# =============================================================================
def test_19_create_custom_callable():
	def custom_factory(key):
		return f'default-{key}'

	d = Dict(_create=True, _creater=custom_factory)
	assert d.missing == 'default-missing'
	assert d['other'] == 'default-other'
	assert 'missing' in d and 'other' in d


# =============================================================================
# 20. __missing__ raises KeyError when _create is False; dot -> AttributeError.
# =============================================================================
def test_20_missing_without_create():
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
# =============================================================================
def test_21_in_no_side_effect():
	d = Dict(_create=True)
	assert 'nope' not in d
	assert 'nope' not in d
	assert len(d) == 0


# =============================================================================
# 22. The instance .hasattr / .getattr methods suppress _create.
# =============================================================================
def test_22_hasattr_getattr_suppress_create():
	d = Dict(_create=True)
	assert d.hasattr('nope') is False
	assert len(d) == 0
	assert d.getattr('nope', 'default') == 'default'
	assert len(d) == 0

	d = Dict({'a': 1})
	assert d.hasattr('a') is True
	assert d.getattr('a') == 1
	assert d.getattr('missing', 'fallback') == 'fallback'


# =============================================================================
# 23. del d.foo and del d['foo'] both remove the key; missing -> errors.
# =============================================================================
def test_23_del():
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
# 24. copy.copy / copy.deepcopy produce independent Dict instances.
# =============================================================================
def test_24_copy_deepcopy():
	d = Dict({'a': 1, 'b': {'nested': [1, 2, 3]}}, _convert=True)
	c = _copy.copy(d)
	assert c == d and c is not d
	assert isinstance(c, Dict)

	dd = _copy.deepcopy(d)
	assert dd == d and dd is not d
	dd.b.nested.append(4)
	assert d.b.nested == [1, 2, 3]


# =============================================================================
# 25. update() with _convert=True converts nested mappings on insert.
# =============================================================================
def test_25_update_converts():
	d = Dict(_convert=True)
	d.update({'a': {'b': 1}, 'c': [{'nested': 2}]})
	assert type(d.a) is Dict
	assert d.a.b == 1
	assert isinstance(d.c, list)
	assert type(d.c[0]) is Dict


# =============================================================================
# 26. _convert=None convert-and-cache.
# =============================================================================
def test_26_convert_and_cache():
	d = Dict({'a': {'b': 1}}, _convert=None)
	assert type(dict.__getitem__(d, 'a')) is dict
	_ = d.a
	assert type(dict.__getitem__(d, 'a')) is Dict


# =============================================================================
# 27. Wrapping a Dict (_convert=False) inside another Dict (_convert=False).
# =============================================================================
def test_27_no_double_wrap():
	inner = Dict({'x': 1}, _convert=False)
	outer = Dict(inner, _convert=False)
	assert outer is inner or outer == inner
	assert outer._s.convert is False


# =============================================================================
# 28. dict.get on a Dict with _create=True does NOT autovivify.
# =============================================================================
def test_28_get_no_autovivify():
	d = Dict(_create=True)
	assert d.get('nope') is None
	assert d.get('nope', 'fallback') == 'fallback'
	assert 'nope' not in d


# =============================================================================
# 29. CommentedMap source — comments preserved when ruamel.yaml is installed.
# =============================================================================
def test_29_commentedmap():
	from ruamel.yaml.comments import CommentedMap
	cm = CommentedMap({'a': 1, 'b': 2})
	cm.yaml_set_comment_before_after_key('a', before='hello')
	d = Dict(cm)
	assert d.a == 1
	assert d.b == 2
	assert d.ca is not None
	assert isinstance(d, CommentedMap)
	assert isinstance(d, Dict)


# =============================================================================
# 30. C-level dict methods route through __getitem__/__setitem__, so conversion
#     stays consistent with the _convert model:
#       reads (get/pop/popitem)  -> convert when _convert is not False
#       writes (update/|=)        -> convert when _convert is True
#       setdefault                -> write (raw under None) then read (caches under None)
# =============================================================================
def test_30_method_conversion_matrix():
	# (mode, read_type, write_stored_type)
	for mode, read_t, write_t in ((None, Dict, dict), (True, Dict, Dict), (False, dict, dict)):
		# reads convert under None/True, raw under False
		assert type(Dict({'a': {'x': 1}}, _convert=mode).get('a')) is read_t
		assert type(Dict({'a': {'x': 1}}, _convert=mode).pop('a')) is read_t
		k, v = Dict({'a': {'x': 1}}, _convert=mode).popitem()
		assert k == 'a' and type(v) is read_t

		# writes (|= and update) convert only under True; under None they store raw
		# (lazy — converts on later read), matching d[k] = {...}
		d = Dict(_convert=mode); d |= {'i': {'z': 1}}
		assert type(dict.__getitem__(d, 'i')) is write_t
		d = Dict(_convert=mode); d.update({'u': {'w': 1}})
		assert type(dict.__getitem__(d, 'u')) is write_t

		# setdefault returns via a read, so its result follows read_t
		assert type(Dict(_convert=mode).setdefault('s', {'y': 1})) is read_t

	# update kwargs path also converts under True
	d = Dict(_convert=True); d.update(a={'b': 1})
	assert type(d.a) is Dict and d.a.b == 1


def test_31_method_semantics():
	# update() with no args is a no-op in every mode (was: dict.update(None) crash)
	for mode in (None, True, False):
		d = Dict({'a': 1}, _convert=mode); d.update()
		assert d == {'a': 1}

	# pop: returns + removes; default on miss; KeyError on miss w/o default
	d = Dict({'a': 1, 'b': 2})
	assert d.pop('a') == 1 and 'a' not in d
	assert d.pop('z', 'def') == 'def'
	try:
		d.pop('z'); raise AssertionError('expected KeyError')
	except KeyError:
		pass

	# setdefault does not overwrite an existing key
	d = Dict({'a': 1})
	assert d.setdefault('a', 999) == 1 and d['a'] == 1

	# popitem is LIFO and raises on empty
	d = Dict({'a': 1, 'b': 2})
	assert d.popitem()[0] == 'b'
	try:
		Dict().popitem(); raise AssertionError('expected KeyError')
	except KeyError:
		pass

	# |= mutates in place and returns self
	d = Dict({'a': 1}); ref = d; d |= {'b': 2}
	assert d is ref and d == {'a': 1, 'b': 2}


# =============================================================================
# 32. _convert/_create/_converter flags: inherit on re-wrap, explicit override,
#     fresh defaults. _create=True is stored as a real flag (normalized) so it
#     survives re-wrap; True routes to the default factory, callables are called.
# =============================================================================
def test_32_flag_inherit_and_override():
	conv = lambda m: Dict(m)
	x = Dict({'a': 1}, _convert=True, _create=True, _converter=conv)

	# _create=True is recorded in _s (not left absent), so it can be inherited
	assert 'create' in x._s

	# re-wrap with no flags inherits convert/create/converter
	z = Dict(x)
	assert z._s.convert is True and z._s.converter is conv
	assert z._s.create is x._s.create and z._s.create     # create inherited (truthy)
	assert type(z.missing) is Dict                        # inherited create still autovivifies

	# explicit values override on re-wrap (including the falsy/None ones)
	assert Dict(x, _convert=None)._s.convert is None
	assert Dict(x, _convert=False)._s.convert is False
	assert Dict(x, _create=False)._s.create is False

	# fresh instance defaults: _convert None, _create off (no autovivify)
	f = Dict({'a': 1})
	assert f._s.convert is None and f._s.create is False


# =============================================================================
# 35. pickle preserves the wrapped source class.
# =============================================================================
def test_35_pickle_preserves_subclass():
	d = Dict(_Special({'a': 1}))
	assert isinstance(d, _Special)
	b = pickle.loads(pickle.dumps(d))
	assert isinstance(b, _Special), f'pickle dropped subclass; got {type(b).__name__}'
	assert b == d


# =============================================================================
# 36. pickle keeps the source class AND its source-managed state (comments) for
#     a CommentedMap — rebuilding from bare data would silently drop comments.
# =============================================================================
def test_36_pickle_preserves_commentedmap():
	from ruamel.yaml.comments import CommentedMap
	cm = CommentedMap({'a': 1, 'b': 2})
	cm.yaml_set_comment_before_after_key('a', before='hello')
	d = Dict(cm)
	assert d.ca.items, 'precondition: comment present before pickle'
	b = pickle.loads(pickle.dumps(d))
	assert b == d
	assert isinstance(b, CommentedMap), f'pickle dropped CommentedMap; got {type(b).__name__}'
	assert b.ca.items, 'pickle dropped CommentedMap comments'


# =============================================================================
# 37. copy() of a wrapped source keeps its class and comments (and must not
#     route through the source's item-by-item copy).
# =============================================================================
def test_37_copy_preserves_commentedmap():
	from ruamel.yaml.comments import CommentedMap
	cm = CommentedMap({'a': 1, 'b': 2})
	cm.yaml_set_comment_before_after_key('a', before='hello')
	d = Dict(cm)
	c = d.copy()  # must not raise
	assert c is not d and c == d
	assert isinstance(c, CommentedMap), f'copy dropped CommentedMap; got {type(c).__name__}'
	assert c.ca.items, 'copy dropped CommentedMap comments'


# =============================================================================
# 38. copy() must not bind the copy's _create to the original instance.
# =============================================================================
def test_38_copy_independent_create():
	d = Dict(_create=True)
	c = d.copy()
	assert c._s.parent is c, "copy's settings are bound to the original instance"
	assert c._s.parent is not d, "copy's settings are bound to the original instance"


# =============================================================================
# 39. Copy(): respect an object's own .copy(); when .copy is the inherited
#     dict.copy (which drops the class), find another way that preserves it.
#     The result is always equal to the source, a distinct object, same type.
# =============================================================================
def test_39_copy_function():
	# plain dict: copied into a distinct plain dict
	d = {'a': 1}
	c = Copy(d)
	assert c == d and c is not d and type(c) is dict

	# dict subclass that inherits dict.copy — dict.copy returns a plain dict and
	# drops the class, so Copy must not settle for it; it preserves the subclass
	class plain_sub(dict): ...
	s = plain_sub({'a': 1})
	assert type(s.copy()) is dict  # precondition: inherited copy loses the class
	c = Copy(s)
	assert c == s and c is not s
	assert type(c) is plain_sub, f'Copy dropped subclass; got {type(c).__name__}'

	# an object with its own .copy() is respected (used as-is)
	class own_copy(dict):
		def copy(self):
			c = type(self)(self)
			c.via_copy = True
			return c
	o = own_copy({'a': 1})
	c = Copy(o)
	assert c == o and c is not o and type(c) is own_copy
	assert getattr(c, 'via_copy', False) is True, 'Copy did not use the object\'s own .copy()'

	# CommentedMap: its own .copy() preserves both the class and the comments
	from ruamel.yaml.comments import CommentedMap
	cm = CommentedMap({'a': 1, 'b': 2})
	cm.yaml_set_comment_before_after_key('a', before='hello')
	c = Copy(cm)
	assert c == cm and c is not cm
	assert isinstance(c, CommentedMap) and c.ca.items


# =============================================================================
# 40. _copy=False on a source that can't be wrapped in place (plain dict / None
#     / list / tuple) raises TypeError, not a bare Exception.
# =============================================================================
def test_40_copy_false_unsupported_source():
	for src in ({'a': 1}, None, [('a', 1)], (('a', 1),)):
		try:
			Dict(src, _copy=False)
			raise AssertionError(f'expected TypeError for _copy=False with {type(src).__name__}')
		except TypeError:
			pass


# =============================================================================
# 41. Self-referential source: a mapping that contains itself must convert
#     without infinite recursion, and the back-reference must point at the
#     wrapper (identity cycle preserved), mirroring munchify's cycle handling.
# =============================================================================
def test_41_self_referential():
	# eager: _convert=True walks the whole structure on insert, so the cycle
	# must be detected rather than recursed into forever.
	d = {'a': 1}
	d['self'] = d
	nd = Dict(d, _convert=True)
	assert nd.a == 1
	assert nd.self is nd                       # back-reference points at the wrapper
	assert type(nd.self) is type(nd)

	# lazy: dot access through the cycle stays finite and identity-stable.
	d2 = {'a': 1}
	d2['self'] = d2
	nd2 = Dict(d2, _convert=None)
	assert nd2.self.a == 1
	assert nd2.self.self.a == 1


# =============================================================================
# 42. _okay_private_keys: a _..._ key listed there is exempt from the "special
#     key" guard and DOES autovivify under _create, while every other _..._ key
#     stays special (no autovivify, dot access -> AttributeError).
# =============================================================================
def test_42_okay_private_keys_autovivify():
	class WithOkay(Dict):
		_okay_private_keys = {'_ok_'}

	d = WithOkay(_create=True)
	# listed private key is exempt -> autovivifies to an empty child
	val = d._ok_
	assert isinstance(val, WithOkay) and len(val) == 0
	assert '_ok_' in d
	# unlisted private key stays special: no autovivify, dot access errors
	try:
		_ = d._nope_
		raise AssertionError('expected AttributeError for unlisted private key')
	except AttributeError:
		pass
	assert '_nope_' not in d


# =============================================================================
# 43. Convert-on-get returns the SAME wrapper on every access (identity-stable),
#     for plain and child-class sources, under _convert=None and _convert=True --
#     NewDict(<already a NewDict>) is idempotent so the get-path never re-wraps.
# =============================================================================
def test_43_nested_mapping_identity_stable():
	for convert in (None, True):
		d = Dict({'x': {'y': 1}}, _convert=convert)
		assert d.x is d.x, f'plain source, _convert={convert}'
		d = Dict(_Special({'x': {'y': 1}}), _convert=convert)
		assert d.x is d.x, f'child source, _convert={convert}'


# =============================================================================
# 44. _Settings: the _s object stores keys prefixed (_convert/_create/...) but
#     exposes them unprefixed via attribute/`in`, favouring keys over attrs.
#     Defaults are convert=None/create=False; converter/creater fall through to
#     bound methods (delegating to the parent) until an explicit value is set.
# =============================================================================
def test_44_settings_object():
	conv = lambda m: Dict(m)
	cr = lambda k: f'v-{k}'
	d = Dict({'a': 1}, _convert=True, _create=True, _converter=conv, _creater=cr)
	s = d._s

	# parent back-reference points at the owning Dict
	assert s.parent is d

	# unprefixed attr, prefixed getitem, and `in` (both spellings) all agree
	assert s.convert is True and s['_convert'] is True
	assert s.create is True and s['_create'] is True
	assert 'convert' in s and '_convert' in s
	assert 'create' in s and '_create' in s

	# an explicitly-set converter/creater is returned verbatim (key over attr)
	assert s.converter is conv and s['_converter'] is conv
	assert s.creater is cr

	# storage is prefixed: raw getitem of the unprefixed name misses
	try:
		_ = s['convert']; raise AssertionError('expected KeyError for unprefixed getitem')
	except KeyError:
		pass

	# dict view exposes the prefixed keys
	assert set(dict(s)) == {'_convert', '_create', '_converter', '_creater'}

	# fresh instance: defaults, and converter/creater fall through to bound
	# methods that delegate to the parent (not stored as keys)
	f = Dict()
	assert f._s.convert is None and f._s.create is False
	assert 'converter' not in f._s and 'creater' not in f._s
	assert getattr(f._s.converter, '__self__', None) is f._s
	assert getattr(f._s.creater, '__self__', None) is f._s

	# setattr writes the prefixed key; unprefixed and prefixed reads track it
	f._s.convert = True
	assert f._s['_convert'] is True and f._s.convert is True and 'convert' in f._s

	# non-str membership is False, never a TypeError
	assert (5 in f._s) is False

	# invalid settings are rejected: attr -> AttributeError, item -> KeyError,
	# and reading an unset non-key attribute -> AttributeError
	try:
		f._s.bogus = 1; raise AssertionError('expected AttributeError setting bogus attr')
	except AttributeError:
		pass
	try:
		f._s['bogus'] = 1; raise AssertionError('expected KeyError setting bogus item')
	except KeyError:
		pass
	try:
		_ = f._s.not_a_setting; raise AssertionError('expected AttributeError reading unset key')
	except AttributeError:
		pass


# =============================================================================
# 45. |/ror/ior are consistent regardless of the other operand's type: the
#     result is always type(self) carrying self's settings, with the other
#     operand only contributing values. (Was: `A | B` delegated to B, so B's
#     _convert=False silently returned an unwrapped plain dict.)
# =============================================================================
def test_45_or_consistency():
	A = Dict({'a': 1}, _convert=True)
	B = Dict({'b': {'c': 1}}, _convert=False)

	# NewDict | NewDict: self (A) wins type + settings; other (B) wins on keys
	r = A | B
	assert type(r) is Dict and r._s.convert is True     # A's True, not B's False
	assert type(r.b) is Dict and r.b.c == 1             # A (convert=True) converts
	assert r.a == 1

	# NewDict | plain dict: identical result shape
	r = A | {'b': {'c': 2}}
	assert type(r) is Dict and r._s.convert is True and type(r.b) is Dict

	# plain dict | NewDict routes through __ror__: self (A) still wins settings,
	# and self's overlapping keys win over the left operand
	r = {'a': 99, 'z': 0} | A
	assert type(r) is Dict and r._s.convert is True
	assert r.a == 1 and r.z == 0

	# _convert=False still yields a NewDict subclass, just no nested conversion
	F = Dict({'x': 1}, _convert=False)
	r = F | {'y': {'k': 1}}
	assert type(r) is Dict and type(r) is not dict and r._s.convert is False
	assert type(dict.__getitem__(r, 'y')) is dict       # nested value left raw
	assert r.x == 1

	# |= mutates in place, keeps self, other's values win
	m = Dict({'a': 1}, _convert=True); ref = m
	m |= {'a': 9, 'b': {'c': 1}}
	assert m is ref and m.a == 9 and type(m.b) is Dict and m.b.c == 1

	# a non-mapping right operand is rejected (NotImplemented -> TypeError)
	try:
		_ = A | 5; raise AssertionError('expected TypeError for | non-mapping')
	except TypeError:
		pass


# =============================================================================
# Registration + run.
# =============================================================================
TESTS = [
	('01. print no recursion', test_01_print_no_recursion),
	('02. dict ops across convert modes', test_02_dict_ops_all_convert_modes),
	('03. subclassing', test_03_subclassing),
	('05. convert flag stored as-passed', test_05_convert_flag_stored_as_passed),
	('06. lazy convert one level', test_06_lazy_convert_one_level),
	('07. nested plain dict is NewDict', test_07_nested_plain_dict_is_newdict),
	('09. multiple inheritance', test_09_multiple_inheritance),
	('10. pickle round-trip', test_10_pickle_roundtrip),
	('11. | merge', test_11_or_merge),
	('12. hasattr missing', test_12_hasattr_missing),
	('13. | precedence', test_13_or_precedence),
	('14. empty is dict + Mapping', test_14_empty_is_dict_and_mapping),
	('15. values unpackable', test_15_values_unpackable),
	('17. mutation propagation', test_17_mutation_propagation),
	('18. _create=True autovivify', test_18_create_true_autovivify),
	('19. _create custom callable', test_19_create_custom_callable),
	('20. __missing__ without create', test_20_missing_without_create),
	('21. in no side effect', test_21_in_no_side_effect),
	('22. hasattr/getattr suppress create', test_22_hasattr_getattr_suppress_create),
	('23. del', test_23_del),
	('24. copy/deepcopy', test_24_copy_deepcopy),
	('25. update converts under True', test_25_update_converts),
	('26. convert-and-cache', test_26_convert_and_cache),
	('27. no double wrap', test_27_no_double_wrap),
	('28. get no autovivify', test_28_get_no_autovivify),
	('29. CommentedMap source preserved', test_29_commentedmap),
	('30. method conversion matrix', test_30_method_conversion_matrix),
	('31. method semantics', test_31_method_semantics),
	('32. flag inherit/override', test_32_flag_inherit_and_override),
	('35. pickle preserves wrapped dict-subclass', test_35_pickle_preserves_subclass),
	('36. pickle preserves wrapped CommentedMap', test_36_pickle_preserves_commentedmap),
	('37. copy() preserves wrapped CommentedMap', test_37_copy_preserves_commentedmap),
	('38. copy() does not bind _create to the original', test_38_copy_independent_create),
	('39. Copy() respects/replaces .copy', test_39_copy_function),
	('40. _copy=False rejects unsupported source', test_40_copy_false_unsupported_source),
	# ('41. self-referential source converts without recursion', test_41_self_referential),
	('42. _okay_private_keys autovivify', test_42_okay_private_keys_autovivify),
	('43. nested mapping identity stable', test_43_nested_mapping_identity_stable),
	('44. _Settings prefixed/unprefixed access', test_44_settings_object),
	('45. |/ror/ior consistency', test_45_or_consistency),
]

failed = _run(TESTS)

if failed:
	print(f'\n{len(failed)} test(s) failed:')
	for _name in failed:
		print(f'  - {_name}')
	import sys
	sys.exit(1)  # @IgnoreException
else:
	print('\nall checks passed')
