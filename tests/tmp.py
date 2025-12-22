from collections import UserDict
from epicstuff import Dict

z = dict(a=1, b=2)
y = Dict(z, _convert=False)

print(z == y)

print(hash(z))
