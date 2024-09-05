# EpicStuff

A few (currently only 3) somewhat useful (Epic) python objects/functions (Stuff)

## Installation

```bash
pip install epicstuff
```

## Bar

Makes using nested progress bars from rich.progress easier

-   Example:

basically replaces

```python
from rich.progress import Progress

with Progress() as progress:
	task = progress.add_task("task", total=100)
	for i in range(100):
		sub_task = progress.add_task("subtask", total=100)
		for j in range(100):
			time.sleep(0.01)  # some task

			progress.update(sub_task, advance=1)

		progress.remove_task(sub_task)
		progress.update(task, advance=1)

```

with

```python
from epicstuff import Bar

with Bar() as bar:
	for i in bar(range(100)):
		for j in bar(range(100), transient=True):
			time.sleep(0.01)  # some task
```

with minor extra features (fancier default bar)

## Dict

Lets you access a dictionary's keys as attributes

### new version

Simpler than [`Bar`](https://pypi.org/project/python-box/) (and faster i think) and with more features (basically only recursive conversion) than [`jdict`](https://pypi.org/project/pyjdict/) (and without some of the "extra" stuff)

-   Example:

```python
from epicstuff import Dict

d = Dict({"a": 1, "b": {"c": 2, "d": 3}})

print(d.b.c)  # 2
```

### old version

"Wraps" a target instead of converting it into a (new) `Dict` object. Useful for when your "target" is say, a `CommentedMap` and you don't want to loose the comments

-   Example:

```python
from epicstuff import Dict

d = Dict(dict(), _convert=False)  # ignore the unexpected-keyword-arg warning

# d._t points to the original dictionary

d.x = 1
```

downsides: currently no recursive "wrapping" and is "messier" than the new Dict in VSCode debugger

## Timer

a simple timer to time execution of code a code segment

-   Example:

```python
from epicstuff import timer

with timer():
	pass  # some code

# outputs: Time elapsed: 0.0 seconds
# message can be changed by passing a string with {} to timer
```

## Stuff

extra functions:

-   `open`: overwriting `open` to use `encoding='utf8'` by default
-   `wrap`: just a renamed `functools.partial`

## TODO:

-   [ ] when doing bar in bar with the second bar being transient, make so that the dots continue from where the previous bar left off
-   [ ] implement auto transient for bar in bar
-   [ ] add and implement simple=False for .Bar.track()

## Stuff:

-   Note to self:
    -   "self install" using `pip install -U -e .`
    -   upload by running `python -m build` then `twine upload dist/*`
