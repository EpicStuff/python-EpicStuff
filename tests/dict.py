from epicstuff import Dict


x = Dict({'a': 1, 'b': {'c': 2, 'd': [3, [[dict(), 3], {'a': dict()}, dict()], {'e': 5}]}})

print(x.b.d)
