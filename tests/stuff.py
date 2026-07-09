import io, unittest
from contextlib import redirect_stdout
from unittest import mock

from parameterized import parameterized

from epicstuff import NewDict as Dict, rmap, timer


def tmp1(key: str):
	if ':' in key:
		parts = key.split(':')
		print('dropping', parts[0], 'from', key)
		return parts[1]
	return key

def tmp2(val: str):
	print('processing', val)
	return '.' + str(val)


class TestStuff(unittest.TestCase):
	def test_rmap(self):
		d = Dict({"a:a": 1, "b:b": [{"c": 2, "d": 3}, 'd']}, _convert=None)  # ignore the unexpected-keyword-arg warning
		assert rmap(d, tmp2, tmp1) == Dict({'a': '.1', 'b': [Dict({'c': '.2', 'd': '.3'}), '.d']})

	def test_getattr_vs_hasattr_bench(self):
		a = 3

		count = 0
		with timer():
			for _ in range(1000000):
				try:
					a.x
				except AttributeError:
					count += 1
		count = 0
		with timer():
			for _ in range(1000000):
				if not hasattr(a, 'x'):
					count += 1

		count = 0
		with timer():
			for _ in range(1000000):
				try:
					a.__bool__
				except AttributeError:
					count += 1
		count = 0
		with timer():
			for _ in range(1000000):
				if not hasattr(a, '__bool__'):
					count += 1

	def test_yields_handle_with_elapsed(self):
		'The context manager yields a handle whose .elapsed is None inside the block and set on exit.'
		with timer() as t:
			self.assertIsNone(t.elapsed)
		self.assertIsNotNone(t.elapsed)

	def test_measures_real_positive_duration(self):
		'A real (unmocked) run records a non-negative elapsed time.'
		with redirect_stdout(io.StringIO()):
			with timer() as t:
				sum(range(1000))
		self.assertGreaterEqual(t.elapsed, 0.0)

	@parameterized.expand([
		('zero', [10.0, 10.0], 0.0),
		('small', [100.0, 100.25], 0.25),
		('large', [5.0, 8.0], 3.0),
	])
	def test_elapsed_exact_with_mocked_clock(self, name, ticks, expected):
		'With perf_counter mocked to fixed start/stop values, elapsed equals their difference exactly.'
		with mock.patch('epicstuff.stuff.perf_counter', side_effect=ticks):
			with redirect_stdout(io.StringIO()):
				with timer() as t:
					pass
		self.assertAlmostEqual(t.elapsed, expected)

	def test_elapsed_set_when_block_raises(self):
		'Elapsed is recorded in the finally clause even if the block raises.'
		t = None
		with mock.patch('epicstuff.stuff.perf_counter', side_effect=[1.0, 3.5]):
			with redirect_stdout(io.StringIO()):
				with self.assertRaises(ValueError):
					with timer() as handle:
						t = handle
						raise ValueError('boom')
		self.assertIsNotNone(t)
		self.assertAlmostEqual(t.elapsed, 2.5)

	def test_prints_formatted_message(self):
		'The elapsed time is formatted into the given message and printed on exit.'
		out = io.StringIO()
		with mock.patch('epicstuff.stuff.perf_counter', side_effect=[0.0, 1.5]):
			with redirect_stdout(out):
				with timer('elapsed={:.3f}'):
					pass
		self.assertEqual(out.getvalue().strip(), 'elapsed=1.500')

	def test_default_message_includes_elapsed(self):
		'The default message prints the measured elapsed value.'
		out = io.StringIO()
		with mock.patch('epicstuff.stuff.perf_counter', side_effect=[0.0, 2.0]):
			with redirect_stdout(out):
				with timer():
					pass
		self.assertIn('2.000000', out.getvalue())


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(TestStuff).debug()
	print('All tests passed')
