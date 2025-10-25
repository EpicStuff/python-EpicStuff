from epicstuff import s
from epicstuff import run_install_trace

def p(*args, **kwargs):
	args = list(args)
	for num, arg in enumerate(args):
		try:
			args[num] = arg.replace('\t', ' \\t ')
		except Exception:
			continue
	print(*args, **kwargs)


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

###########
p('---')

assert 'a' + s('b') == 'ab'
assert s('a') + s('b') == 'ab'

assert s('a') + 'b' == 'ab'
assert s('a') + '\nb' == 'a\nb'
assert '\na' + s('b') == 'ab'

assert s('a\na\n') + 'b\nb' == 'a\na\nb\nb'
assert s('a\na') + 'b' == 'a\nab'
assert s('a') + 'b\nb' == 'ab\nb'


assert s('a') + 'b' == 'ab'
assert s('a') + '\nb' == 'a\nb'
assert s('\na\na\n') + s('b\nb') == 'a\na\nb\nb'
assert s('a\na') + 'b' == 'a\nab'
assert s('a') + 'b\nb' == 'ab\nb'
assert s('') + 'x' == 'x'
assert 'x' + s('') == 'x'
assert 'x\n' + s('y') == 'x\ny'
assert s('x') + '\ny' == 'x\ny'

p('---')

string = s('''line 1
		line 2
			line 3
''') + 'line 4'

print(string)
