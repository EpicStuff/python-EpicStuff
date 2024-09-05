'''misc stuff'''
from functools import partial as wrap

open = wrap(open, encoding='utf8')  # pylint: disable=redefined-builtin
