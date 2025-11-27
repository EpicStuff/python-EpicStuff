from epicstuff import BoxDict


left = BoxDict({'a': 1})

result = left | {'b': 2}

assert isinstance(result, BoxDict)
assert result is not left
assert result == {'a': 1, 'b': 2}


right = BoxDict({'b': 2})

result = {'a': 1} | right

assert isinstance(result, BoxDict)
assert result == {'a': 1, 'b': 2}


target = BoxDict({'a': 1})
original_id = id(target)

target |= {'b': 2}

assert isinstance(target, BoxDict)
assert id(target) == original_id
assert target == {'a': 1, 'b': 2}
