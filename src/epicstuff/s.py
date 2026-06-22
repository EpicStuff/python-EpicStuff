import re
import warnings
from inspect import cleandoc
from typing import Self


class String(str):
	'Auto formatting string.'

	__slots__ = ('_leading_newline', '_trailing_newline')
	_leading_newline: bool
	_trailing_newline: bool

	def __new__(cls, s: object, _leading_newline: bool | None = None, _trailing_newline: bool | None = None) -> Self:
		# new line priority: 1. explicit arg, 2. from s if is String, 3. from str

		if isinstance(s, cls):
			text = str(s)  # already formatted; reformatting is idempotent, so skip it
		else:
			raw = str(s)
			# warn when indentation uses both tabs and spaces (within a line or across
			# lines): cleandoc's expandtabs then our retab resolve those ambiguously. Check
			# the raw input up front, before cleandoc rewrites the indentation.
			indents = ''.join(re.findall(r'(?m)^([ \t]*)\S', raw))
			if '\t' in indents and ' ' in indents:
				warnings.warn('mixed indentation: indentation uses both tabs and spaces', stacklevel=2)
			# cleandoc expandtabs()-es every line to 8 spaces before dedenting, so its output
			# is always space-indented. Convert each line's *leading* spaces back to tabs
			# (8 -> \t), leaving any partial group and all mid-content spaces untouched.
			def retab(match: re.Match[str]) -> str:
				tabs, spaces = divmod(len(match.group()), 8)
				return '\t' * tabs + ' ' * spaces
			text = re.sub(r'^ +', retab, cleandoc(raw), flags=re.MULTILINE)
		self = super().__new__(cls, text)
		self._leading_newline = _leading_newline if _leading_newline is not None else s._leading_newline if isinstance(s, cls) else str(s).startswith('\n')
		self._trailing_newline = _trailing_newline if _trailing_newline is not None else s._trailing_newline if isinstance(s, cls) else str(s).endswith('\n')
		return self

	def __add__(self, other: object) -> Self:
		other = self.__class__(other)
		# both operands are already formatted and the join keeps their margin-0 anchors,
		# so build directly via str.__new__ instead of re-running cleandoc on the result
		result = str.__new__(self.__class__,
			str(self) +  # str() to prevent recursion
			('\n' if self._trailing_newline or other._leading_newline else '') +
			str(other),
		)
		result._leading_newline = self._leading_newline
		result._trailing_newline = other._trailing_newline
		return result
	__iadd__ = __add__
	def __radd__(self, other: object) -> Self:  # left + self, when left isn't a String
		return self.__class__(other) + self

	def __repr__(self) -> str:
		return 's(' + super().__repr__() + ')'
