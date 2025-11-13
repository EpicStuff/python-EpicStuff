# ruff: noqa: S101
from inspect import signature

from epicstuff import perm


def f(a, b=2, *, c=3) -> int:
	return a + b + c


def g(*args, **kwargs):
	return (args, kwargs)


def f_posonly(a, b, /, c=0):
	# a and b are positional-only; c is optional
	return a * 10 + b * 100 + c

def test_optional_ignore_and_overwrite_true():
	w = perm(f)
	# Extra positionals ignored, keyword overwrites positional b
	assert w(1, 99, 100, b=4, c=5, d=6) == 1 + 4 + 5
	# Overwrite b by keyword
	assert w(1, b=9, c=5) == 1 + 9 + 5
	# Unknown keyword ignored
	assert w(1, 7, z=9) == 1 + 7 + 3


def test_positional_overwrite_defaults_false_keyword_override_true():
	w = perm(f, positional_overwrite_defaults=False)
	assert w(1, 8) == 1 + 2 + 3  # default b retained


def test_positional_overwrite_defaults_true_keyword_override_false():
	w = perm(f, keyword_overrides_passed_positional=False)
	assert w(1, 99, b=4) == 1 + 99 + 3  # keyword cannot override


def test_positional_overwrite_defaults_false_keyword_override_false():
	w = perm(f, False, False)
	assert w(1, 99, b=4) == 1 + 4 + 3  # positional ignored, keyword ignored for consumed default


def test_varargs_passthrough():
	w = perm(g)
	args, kwargs = w(1, 2, a=3, b=4, extra=5)
	assert args == (1, 2)
	assert kwargs == {'a': 3, 'b': 4, 'extra': 5}
	# no args/kwargs
	w()


test_optional_ignore_and_overwrite_true()
test_positional_overwrite_defaults_false_keyword_override_true()
test_positional_overwrite_defaults_true_keyword_override_false()
test_positional_overwrite_defaults_false_keyword_override_false()
test_varargs_passthrough()
