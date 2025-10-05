'''misc stuff'''
from functools import partial as wrap

open = wrap(open, encoding='utf8')  # noqa: A001  # pylint: disable=redefined-builtin
