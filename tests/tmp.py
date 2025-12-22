from collections import UserDict, abc
from epicstuff import Dict
import orjson

x = Dict(dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}), _convert=False)

print(dict(x))
print(isinstance(x, Dict), isinstance(x, dict), isinstance(x, abc.Mapping))

z = dict(a=1, b=2)
y = Dict(z, _convert=False)
print(z.values())
print(y.values())

print(orjson.dumps(x, default=dict))
