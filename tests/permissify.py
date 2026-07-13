import unittest

from epicstuff import perm
from parameterized import parameterized


def f(a, b=2, *, c=3) -> int:
	return a + b + c


def g(*args, **kwargs):
	return (args, kwargs)


def f_posonly(a, b, /, c=0):
	# a and b are positional-only; c is optional
	return a * 10 + b * 100 + c


class TestPermissify(unittest.TestCase):
	@parameterized.expand([
		# name, perm kwargs, call args, call kwargs, expected
		# Extra positionals ignored, keyword overwrites positional b
		('optional_ignore_overwrite_true_extra', {}, (1, 99, 100), {'b': 4, 'c': 5, 'd': 6}, 1 + 4 + 5),
		# Overwrite b by keyword
		('optional_ignore_overwrite_true_kw', {}, (1,), {'b': 9, 'c': 5}, 1 + 9 + 5),
		# Unknown keyword ignored
		('optional_ignore_overwrite_true_unknown_kw', {}, (1, 7), {'z': 9}, 1 + 7 + 3),
		# default b retained when positional_overwrite_defaults=False
		('positional_overwrite_defaults_false', {'positional_overwrite_defaults': False}, (1, 8), {}, 1 + 2 + 3),
		# keyword cannot override when keyword_overrides_passed_positional=False
		('keyword_override_false', {'keyword_overrides_passed_positional': False}, (1, 99), {'b': 4}, 1 + 99 + 3),
	])
	def test_perm_f(self, name, perm_kwargs, args, kwargs, expected) -> None:
		w = perm(f, **perm_kwargs)
		assert w(*args, **kwargs) == expected

	def test_positional_overwrite_defaults_false_keyword_override_false(self) -> None:
		w = perm(f, False, False)
		assert w(1, 99, b=4) == 1 + 4 + 3  # positional ignored, keyword ignored for consumed default

	def test_varargs_passthrough(self) -> None:
		w = perm(g)
		args, kwargs = w(1, 2, a=3, b=4, extra=5)
		assert args == (1, 2)
		assert kwargs == {'a': 3, 'b': 4, 'extra': 5}
		# no args/kwargs
		w()


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(TestPermissify).debug()
	print('All tests passed')
