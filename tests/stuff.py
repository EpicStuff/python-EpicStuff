from epicstuff import Dict

d = Dict({"a": 1, "b": {"c": 2, "d": 3}}, _convert=False)  # ignore the unexpected-keyword-arg warning

# d._t points to the original dictionary

print(d.b)  # {'c': 2, 'd': 3}
