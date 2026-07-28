import unittest

from epicstuff import s
from parameterized import parameterized


def p(*args, **kwargs) -> None:
	args = list(args)
	for num, arg in enumerate(args):
		try:
			args[num] = arg.replace('\t', ' \\t ')
		except Exception:
			continue
	print(*args, **kwargs)


# each case: (name, actual, expected) — actual is produced eagerly by String operations
CASES = [
	("'a' + s('b')", 'a' + s('b'), 'ab'),
	("s('a') + s('b')", s('a') + s('b'), 'ab'),
	("s('a') + 'b'", s('a') + 'b', 'ab'),
	("s('a') + '\\nb'", s('a') + '\nb', 'a\nb'),
	("'\\na' + s('b')", '\na' + s('b'), 'ab'),
	("s('a\\na\\n') + 'b\\nb'", s('a\na\n') + 'b\nb', 'a\na\nb\nb'),
	("s('a\\na') + 'b'", s('a\na') + 'b', 'a\nab'),
	("s('a') + 'b\\nb'", s('a') + 'b\nb', 'ab\nb'),
	("s('a') + 'b' (2)", s('a') + 'b', 'ab'),
	("s('a') + '\\nb' (2)", s('a') + '\nb', 'a\nb'),
	("s('\\na\\na\\n') + s('b\\nb')", s('\na\na\n') + s('b\nb'), 'a\na\nb\nb'),
	("s('a\\na') + 'b' (2)", s('a\na') + 'b', 'a\nab'),
	("s('a') + 'b\\nb' (2)", s('a') + 'b\nb', 'ab\nb'),
	("s('') + 'x'", s('') + 'x', 'x'),
	("'x' + s('')", 'x' + s(''), 'x'),
	("'x\\n' + s('y')", 'x\n' + s('y'), 'x\ny'),
	("s('x') + '\\ny'", s('x') + '\ny', 'x\ny'),
]


class Main(unittest.TestCase):
	@parameterized.expand(CASES)
	def test_add(self, name, actual, expected) -> None:
		self.assertEqual(actual, expected)

	def test_demo_runs(self) -> None:
		'Exercise the formatting/concatenation demos; any breakage raises.'
		tmp = s('''Line 1
			Line 2
				Line 3
			Line 4
		''')

		p(tmp)

		p('---')

		p(tmp + '''
			Appended line
				With tab
					and Another tab
		''')

		p('---')

		p('Start ' + tmp)

		p('---')

		tmp += '\nIn-place appended line\n\tWith tab\n\t\tand Another tab\n'
		p(tmp)

		p('---')

		string = s('''line 1
				line 2
					line 3
		''') + 'line 4'

		p(string)


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(Main).debug()
	print('All tests passed')
