'''allowing multiple rich.progress.track'''
from itertools import cycle
from operator import length_hint
from threading import Thread
from time import sleep
from typing import Iterable, Sequence, Union

from rich.progress import MofNCompleteColumn, Progress, ProgressType, SpinnerColumn, TaskID, TimeElapsedColumn


class Bar():
	'''Container for an auto-updating progress bar(s).

    Args:
        auto_refresh (bool, optional): Enable auto refresh. If disabled, you will need to call `refresh()`.
        refresh_per_second (Optional[float], optional): Number of times per second to refresh the progress information or None to use default (10). Defaults to None.
        speed_estimate_period: (float, optional): Period (in seconds) used to calculate the speed estimate. Defaults to 30.
        expand (bool, optional): Expand tasks table to fit width. Defaults to False.
    '''
	def __init__(self, auto_refresh: bool = True, refresh_per_second: float = 10, speed_estimate_period: float = 30.0, expand: bool = False) -> None:
		self.progress = None
		self.auto_refresh = auto_refresh
		self.refresh_per_second = refresh_per_second
		self.speed_estimate_period = speed_estimate_period
		self.expand = expand
	def __enter__(self):
		self.progress = Progress(MofNCompleteColumn(), SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), auto_refresh=self.auto_refresh, refresh_per_second=self.refresh_per_second, speed_estimate_period=self.speed_estimate_period, expand=self.expand)
		self.progress.start()
		return self.track
	def __exit__(self, exc_type, exc_value, traceback):
		self.progress.stop()
	def _cycle(self, desc: str, task: TaskID, delay: float = 0.5):
		'cycle description through ..., , ., and ..'
		desc_s = cycle([f'{desc}...', f'{desc}   ', f'{desc}.  ', f'{desc}.. '])
		# while task is ongoing
		while task in self.progress.task_ids:
			# cycle the description to the next one
			self.progress.update(task, description=next(desc_s))
			# wait delay seconds
			sleep(delay)
	def track(self, sequence: Union[Iterable[ProgressType], Sequence[ProgressType]], description: str = "Working", transient: bool = False) -> Iterable[ProgressType]:
		'''Track progress by iterating over a sequence.

		Args:
			sequence (Sequence[ProgressType]): A sequence of values you want to iterate over and track progress.
			total: (float, optional): Total number of steps. Default is len(sequence).
			task_id: (TaskID): Task to track. Default is new task.
			description: (str, optional): Description of task, if new task is created.
			update_period (float, optional): Minimum time (in seconds) between calls to update(). Defaults to 0.1.

		Returns:
			Iterable[ProgressType]: An iterable of values taken from the provided sequence.
		'''
		task_id = self.progress.add_task(description, total=float(length_hint(sequence)) or None)
		Thread(target=self._cycle, args=(description, task_id), daemon=True).start()

		for value in sequence:
			yield value
			self.progress.advance(task_id, 1)
			self.progress.refresh()

		# hide the task after done if it's transient
		if transient:
			self.progress.remove_task(task_id)


with Bar() as bar:
	for _ in bar(range(100)):
		for _ in bar(range(100), transient=True):
			pass
