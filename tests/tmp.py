from epicstuff import Dict, timer

x = Dict()
tmp = 'abc'
with timer():
	for i in range(1000000):
		tmp in x.__dict__

with timer():
	for i in range(1000000):
		hasattr(x, tmp)
