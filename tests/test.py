from EpicStuff import Bar

with Bar() as bar:
	for _ in bar(range(100)):
		for _ in bar(range(100), transient=True):
			pass