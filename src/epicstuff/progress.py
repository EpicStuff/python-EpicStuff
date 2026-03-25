import itertools, threading, time
from collections.abc import Callable, Iterable, Sequence
from operator import length_hint
from types import TracebackType

from rich.progress import MofNCompleteColumn, Progress, ProgressType, SpinnerColumn, TaskID, TimeElapsedColumn


class Bar:
	'''Container for an auto-updating progress bar(s).

	Args:
	- auto_refresh (bool, optional): Enable auto refresh. If disabled, you will need to call `refresh()`.
	- refresh_per_second (Optional[float], optional): Number of times per second to refresh the progress information or None to use default (10). Defaults to None.
	- speed_estimate_period: (float, optional): Period (in seconds) used to calculate the speed estimate. Defaults to 30.
	- expand (bool, optional): Expand tasks table to fit width. Defaults to False.

	'''

	def __init__(self, auto_refresh: bool = True, refresh_per_second: float = 10, speed_estimate_period: float = 30.0, expand: bool = False, add_columns: dict[int, Callable] | None = None, remove_columns: list[int] | None = None) -> None:
		self.tasks = []
		self.progress = None
		self.auto_refresh = auto_refresh
		self.refresh_per_second = refresh_per_second
		self.speed_estimate_period = speed_estimate_period
		self.expand = expand
		self.add_columns = add_columns or {}
		self.remove_columns = remove_columns or []
	def __enter__(self) -> Callable:
		columns = [MofNCompleteColumn(), SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn()]
		for index, column in self.add_columns.items():
			columns.insert(index, column)
		for index in self.remove_columns:
			del columns[index]
		self.progress = Progress(*columns, auto_refresh=self.auto_refresh, refresh_per_second=self.refresh_per_second, speed_estimate_period=self.speed_estimate_period, expand=self.expand)
		self.progress.start()
		return self.track
	def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
		self.progress.stop()
	def _cycle(self, desc: str, task: TaskID, delay: float = 0.5) -> None:
		'Cycle description through ..., , ., and ..'
		desc_s = itertools.cycle([f'{desc}   ', f'{desc}.  ', f'{desc}.. ', f'{desc}...'])
		# while task is ongoing
		while task in self.progress.task_ids:
			# cycle the description to the next one
			self.progress.update(task, description=next(desc_s))
			# wait delay seconds
			time.sleep(delay)
	def track(self, sequence: Iterable[ProgressType] | Sequence[ProgressType], description: str = 'Working', total: float | None = -1, transient: bool = False, cycle: bool = True) -> Iterable[ProgressType]:
		'''Track progress by iterating over a sequence.

		Args:
			sequence (Sequence[ProgressType]): A sequence of values you want to iterate over and track progress.
			description: (str, optional): Description of task, if new task is created.
			total: (float, optional): Total number of steps. Default is len(sequence).
			transient: (bool, optional): Clear the progress on exit. Defaults to False.
			cycle: (bool, optional): Whether to cycle the description with dots while the task is ongoing. Defaults to True.

		Returns:
			Iterable[ProgressType]: An iterable of values taken from the provided sequence.

		'''
		task_id = self.progress.add_task(description, total=total if total != -1 else float(length_hint(sequence)) or None)
		self.tasks.append(task_id)
		if cycle:
			threading.Thread(target=self._cycle, args=(description, task_id), daemon=True).start()

		for value in sequence:
			yield value
			self.progress.advance(task_id, 1)
			self.progress.refresh()

		# hide the task after done if it's transient
		if transient:
			self.progress.remove_task(task_id)
		# if not transient, remove the dots
		else:
			self.progress.update(task_id, description=f'{description}   ')
