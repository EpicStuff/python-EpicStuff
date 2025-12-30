from collections import UserString
from inspect import cleandoc
from typing import Self


class String(UserString):
	'Auto formatting string.'

	def __init__(self, s: object, _leading_newline: bool | None = None, _trailing_newline: bool | None = None) -> None:
		s = str(s)
		# new line priority: 1. explicit arg, 2. from s if is String, 3. from str
		self._leading_newline = _leading_newline if _leading_newline is not None else s._leading_newline if isinstance(s, String) else s.startswith('\n')
		self._trailing_newline = _trailing_newline if _trailing_newline is not None else s._trailing_newline if isinstance(s, String) else s.endswith('\n')
		super().__init__(cleandoc(s).replace('        ', '\t'))
		self.str = self.data  # for easier access
	def __add__(self, other: object) -> Self:
		other = self.__class__(other)
		return self.__class__(
			self.data +
			('\n' if self._trailing_newline or other._leading_newline else '') +
			other.data,
			_leading_newline=self._leading_newline,
			_trailing_newline=other._trailing_newline,
		)
	def __radd__(self, other: object) -> Self:
		other = self.__class__(other)
		return self.__class__(
			other.data +
			('\n' if other._trailing_newline or self._leading_newline else '') +
			self.data,
			_leading_newline=other._leading_newline,
			_trailing_newline=self._trailing_newline,
		)
	def __iadd__(self, other: object) -> Self:
		other = self.__class__(other)
		self.data += ('\n' if self._trailing_newline or other._leading_newline else '') + other.data
		self._trailing_newline = other._trailing_newline
		return self
	def __repr__(self) -> str:
		return 's(' + super().__repr__() + ')'
