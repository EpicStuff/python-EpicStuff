from collections.abc import Generator
from contextlib import contextmanager
from time import time


@contextmanager
def timer(message: str = 'Time elapsed: {} seconds') -> Generator:
	'''To be used with `with` to time a block of code.

	Example:
	```python
	with timer():
		pass  # some code
	```

	'''
	start = time()
	yield
	print(message.format(time() - start))
