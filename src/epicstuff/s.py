from inspect import cleandoc
from typing import Self


class String(str):
	'Auto formatting string.'

	__slots__ = ('_leading_newline', '_trailing_newline')
	_leading_newline: bool
	_trailing_newline: bool

	def __new__(cls, s: object, _leading_newline: bool | None = None, _trailing_newline: bool | None = None) -> Self:
		# new line priority: 1. explicit arg, 2. from s if is String, 3. from str
		
		self = super().__new__(cls, cleandoc(str(s)).replace('        ', '\t'))
		self._leading_newline = _leading_newline if _leading_newline is not None else s._leading_newline if isinstance(s, cls) else str(s).startswith('\n')
		self._trailing_newline = _trailing_newline if _trailing_newline is not None else s._trailing_newline if isinstance(s, cls) else str(s).endswith('\n')
		return self

	def __add__(self, other: object) -> Self:
		other = self.__class__(other)
		return self.__class__(
			str(self) +  # str() to prevent recursion
			('\n' if self._trailing_newline or other._leading_newline else '') +
			str(other),
			_leading_newline=self._leading_newline,
			_trailing_newline=other._trailing_newline,
		)
	def __radd__(self, other: object) -> Self:
		other = self.__class__(other)
		return self.__class__(
			str(other) +
			('\n' if other._trailing_newline or self._leading_newline else '') +
			str(self),  # str() to prevent recursion
			_leading_newline=other._leading_newline,
			_trailing_newline=self._trailing_newline,
		)
	def __iadd__(self, other: object) -> Self:
		other = self.__class__(other)
		result = str(self) + ('\n' if self._trailing_newline or other._leading_newline else '') + str(other)  # str() to prevent recursion
		return self.__class__(result, _leading_newline=self._leading_newline, _trailing_newline=other._trailing_newline)

	def __repr__(self) -> str:
		return 's(' + super().__repr__() + ')'
