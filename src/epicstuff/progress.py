import itertools, threading
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from operator import length_hint
from types import TracebackType
from typing import Self

from rich.progress import MofNCompleteColumn, Progress, ProgressColumn, ProgressType, SpinnerColumn, TaskID, TimeElapsedColumn


@dataclass
class Bar:
	'''Container for an auto-updating progress bar(s).

	Args:
	- auto_refresh (bool, optional): Enable auto refresh. If disabled, you will need to call `refresh()`.
	- refresh_per_second (float, optional): Number of times per second to refresh the progress information or None to use default (10). Defaults to None.
	- speed_estimate_period: (float, optional): Period (in seconds) used to calculate the speed estimate. Defaults to 30.
	- expand (bool, optional): Expand tasks table to fit width. Defaults to False.
	- add_columns (dict[int, ProgressColumn], optional): Each value in dict provided will be inserted into columns at the key position.
	- remove_columns (list[int], optional): For each index provided, the column will be removed. Note, the index is calculated before add_columns are added.

	'''
	auto_refresh: bool = True
	refresh_per_second: float = 10
	speed_estimate_period: float = 30.0
	expand: bool = False
	add_columns: dict[int, ProgressColumn] = field(default_factory=dict)
	remove_columns: list[int] = field(default_factory=list)

	tasks: list[TaskID] = field(default_factory=list, init=False, repr=False, compare=False)
	progress: Progress = field(init=False, repr=False, compare=False)

	def __enter__(self) -> Self:
		columns: list[ProgressColumn] = [MofNCompleteColumn(), SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn()]
		for index in sorted(self.remove_columns, reverse=True):
			del columns[index]
		for index, column in self.add_columns.items():
			columns.insert(index, column)
		self.progress = Progress(*columns, auto_refresh=self.auto_refresh, refresh_per_second=self.refresh_per_second, speed_estimate_period=self.speed_estimate_period, expand=self.expand)
		self.progress.start()
		return self
	def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
		self.progress.stop()
	def _cycle(self, desc: str, task: TaskID, stop: threading.Event, delay: float = 0.5) -> None:
		'Cycle description through ..., , ., and .. until stop is set.'
		desc_s = itertools.cycle([f'{desc}   ', f'{desc}.  ', f'{desc}.. ', f'{desc}...'])
		# wait delay seconds, then cycle the description to the next one, until stopped
		while self.progress.live.is_started and not stop.wait(delay):
			self.progress.update(task, description=next(desc_s))
	def __call__(self, sequence: Iterable[ProgressType], description: str = 'Working', total: float | None = -1, transient: bool = False, cycle: bool = True) -> Iterator[ProgressType]:
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
		stop = threading.Event()
		thread = threading.Thread(target=self._cycle, args=(description, task_id, stop), daemon=True) if cycle else None
		if thread:
			thread.start()

		completed = False
		try:
			for value in sequence:
				yield value
				self.progress.advance(task_id, 1)
				self.progress.refresh()
			completed = True
		finally:
			# stop the dots animation in every case (normal, break, or error)
			if thread:
				stop.set()
				thread.join()
			# only clear a transient bar on clean completion; on break/error leave it on screen, just without dots
			if transient and completed:
				self.progress.remove_task(task_id)
				self.tasks.remove(task_id)
			else:
				self.progress.update(task_id, description=f'{description}   ')
