# EpicStuff

A few somewhat useful (Epic) python objects/functions (Stuff)

## Installation

```bash
pip install epicstuff
```

## Dict

Lets you access a dictionary's keys as attributes

### JDict version

Points to a target instead of converting it into a (new) `Dict` object. Useful for when your "target" is say, a `CommentedMap` and you don't want to loose the comments.

- Example:

```python
from epicstuff import Dict

d = Dict({})

d.x = 1
```

### BoxDict version

Simpler (less features) than [`Box`](https://pypi.org/project/python-box/) (and faster i think) but with more features (recursive conversion and creation on access) than [`jdict`](https://pypi.org/project/pyjdict/) (and without some of the "extra" stuff)

- Example:

```python
from epicstuff import Dict

d = Dict({"a": 1, "b": {"c": 2, "d": 3}}, _convert=None)

print(d.b.c)  # 2
```

## Rich Trace

Easily install terminal-wide `rich.traceback` and use helpers to ensure pretty tracebacks with async functions.

- Example:

```python
from epicstuff import run_install_trace
```

- or:

```python
from epicstuff import rich_trace

@rich_trace
async def some_func():
	raise Exception
some_func()
```

- or:

```python
@rich_trace(_return=0)
async def some_func():
	raise Exception
some_func()
```

- or:

```python
with rich_trace():
	raise Exception
```

## Bar

Makes using nested progress bars from rich.progress easier

- Example:

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


## Timer

a simple timer to time execution of code a code segment

- Example:

```python
from epicstuff import timer

with timer():
	pass  # some code

# outputs: Time elapsed: 0.0 seconds
# message can be changed by passing a string with {} to timer
```

## s

An autoformatting string. Removes extra indent and leading/trailing newlines.

- Example:

```python
from epicstuff import s

string = s('''
	line 1
		line 2
			line 3
''') + 'line 4'

print(s)
# line 1
# 	line 2
# 		line 3
# line 4
```

## Permissify

make function ignore extra arguments instead of raising an error.

- Example:

```python
from epicstuff import perm

def tmp(a, b=2): ...

perm(tmp)(1, 2, b=3, c=5)  # this will run without raising TypeError
```

## Stuff

extra functions:

- `open`: overwriting `open` with `Path.open` and `encoding='utf8'`
- `wrap`: just a renamed `functools.partial`
- `rmap`: `map` but recursive for lists and dicts
	- takes `list` or `dict` and 2 functions, will apply function 1 to all keys and function 2 to all values
- `Tee`: Text stream that writes to multiple underlying streams. (Example: redirect stdout to terminal and a file)
- `Pointer`: an object you can kinda use like a pointer. (Example `number = Pointer(5), number._t = 6`)

## TODO:

- [ ] when doing bar in bar with the second bar being transient, make so that the dots continue from where the previous bar left off
- [ ] implement auto transient for bar in bar
- [ ] add and implement simple=False for .Bar.track()

## Stuff:

- Note to self:
	- "self install" using `pip install -U -e .`
	- upload by running `python -m build` then `twine upload --skip-existing dist/*`
