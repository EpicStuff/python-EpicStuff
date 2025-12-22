from collections import UserDict
from epicstuff import Dict

x = Dict(dict([('a', 1), ('b', 2)], l={'b': {'c': [3, {}]}}), _convert=False)

z = dict(a=1, b=2)
y = Dict(z, _convert=False)
print(z == y)
