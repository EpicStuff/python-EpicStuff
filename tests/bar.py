import time, unittest

from epicstuff import Bar
from parameterized import parameterized


class TestBar(unittest.TestCase):
	'''Behavioural tests for epicstuff.Bar (a rich.progress.Progress wrapper).

	Bars are built with auto_refresh=False and iterated with cycle=False so no
	live refresh loop or description-cycling thread runs during assertions.
	'''

	def test_yields_input_values(self) -> None:
		'bar(sequence) yields exactly the values of the wrapped sequence.'
		with Bar(auto_refresh=False) as bar:
			out = list(bar(range(5), cycle=False))
		self.assertEqual(out, [0, 1, 2, 3, 4])

	def test_tracks_task_and_completes(self) -> None:
		'Iterating a bar registers one task and advances it to finished.'
		with Bar(auto_refresh=False) as bar:
			list(bar(range(5), cycle=False))
			self.assertEqual(len(bar.tasks), 1)
			task = bar.progress.tasks[0]
			self.assertEqual(task.completed, 5)
			self.assertEqual(task.total, 5.0)
			self.assertTrue(task.finished)

	def test_total_defaults_to_length(self) -> None:
		'With no explicit total, total is taken from the sequence length hint.'
		with Bar(auto_refresh=False) as bar:
			list(bar(range(7), cycle=False))
			self.assertEqual(bar.progress.tasks[0].total, 7.0)

	def test_explicit_total_override(self) -> None:
		'An explicit total is used verbatim, so the task is not finished after fewer steps.'
		with Bar(auto_refresh=False) as bar:
			list(bar(range(3), total=10, cycle=False))
			task = bar.progress.tasks[0]
			self.assertEqual(task.total, 10)
			self.assertEqual(task.completed, 3)
			self.assertFalse(task.finished)

	@parameterized.expand([
		# (transient, break_early, expect_remaining_tasks)
		('transient_complete', True, False, 0),   # transient + clean completion -> task removed
		('transient_break', True, True, 1),       # transient + break -> task left on screen
		('nontransient_complete', False, False, 1),
		('nontransient_break', False, True, 1),
	])
	def test_transient_removal(self, name, transient, break_early, expected_remaining) -> None:
		'A transient bar is removed only on clean completion; a break/non-transient bar stays.'
		with Bar(auto_refresh=False) as bar:
			for x in bar(range(10), transient=transient, cycle=False):
				if break_early and x == 2:
					break
			self.assertEqual(len(bar.tasks), expected_remaining)
			self.assertEqual(len(bar.progress.tasks), expected_remaining)

	def test_nested_bars(self) -> None:
		'Nested iteration (outer + transient inner) yields the full product; only the outer task remains.'
		with Bar(auto_refresh=False) as bar:
			out = []
			for i in bar(range(2), cycle=False):
				for j in bar(range(3), transient=True, cycle=False):
					out.append((i, j))
			self.assertEqual(out, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)])
			self.assertEqual(len(bar.tasks), 1)

	def test_remove_columns(self) -> None:
		'remove_columns drops the requested column from the default column set.'
		with Bar(auto_refresh=False) as base:
			base_count = len(base.progress.columns)
		with Bar(auto_refresh=False, remove_columns=[0]) as bar:
			self.assertEqual(len(bar.progress.columns), base_count - 1)

	def test_visual_smoke(self) -> None:
		'The original bar.py visual scenario still runs end-to-end (fast, no assertion on output).'
		with Bar(auto_refresh=False) as bar:
			for _i in bar(range(3), cycle=False):
				for _j in bar(range(3), transient=True, cycle=False):
					time.sleep(0)  # some task


if __name__ == '__main__':
	unittest.TestLoader().loadTestsFromTestCase(TestBar).debug()
	print('All tests passed')
