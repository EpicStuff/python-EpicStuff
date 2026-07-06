import re, warnings
from inspect import cleandoc
from typing import Self


class String(str):
	'Auto formatting string.'

	__slots__ = ('_leading_newline', '_trailing_newline')
	_leading_newline: bool
	_trailing_newline: bool

	def __new__(cls, s: str, _leading_newline: bool | None = None, _trailing_newline: bool | None = None) -> Self:
		# new line priority: 1. explicit arg, 2. from s if is String, 3. from str
		string = s
		if not isinstance(s, cls):
			raw = str(s)
			# warn when indentation uses both tabs and spaces (within a line or across
			indents = ''.join(re.findall(r'(?m)^([ \t]*)\S', raw))
			if '\t' in indents and ' ' in indents:
				warnings.warn('Mixed Indentation Detected', stacklevel=2)
			# cleandoc converts tabs to 8 spaces, undo
			def retab(match: re.Match[str]) -> str:
				tabs, spaces = divmod(len(match.group()), 8)
				return '\t' * tabs + ' ' * spaces
			string = re.sub(r'^ +', retab, cleandoc(raw), flags=re.MULTILINE)
		self = super().__new__(cls, string)
		self._leading_newline = _leading_newline if _leading_newline is not None else s._leading_newline if isinstance(s, cls) else str(s).startswith('\n')
		self._trailing_newline = _trailing_newline if _trailing_newline is not None else s._trailing_newline if isinstance(s, cls) else str(s).endswith('\n')
		return self

	def __add__(self, other: str) -> Self:
		# Called by self + other
		other = self.__class__(other)
		result = str.__new__(
			self.__class__,
			str(self) +  # str() to prevent recursion
			('\n' if self._trailing_newline or other._leading_newline else '') +
			str(other),
		)
		result._leading_newline = self._leading_newline
		result._trailing_newline = other._trailing_newline
		return result
	def __radd__(self, other: str) -> Self:
		# Called by other + self, when other isn't a String
		return self.__class__(other) + self  # convert then call __add__
	def __iadd__(self, other: str) -> Self:
		# Called by self += other
		return self + other  # call __add__

	def __repr__(self) -> str:
		return 's(' + super().__repr__() + ')'
