'''allowing multiple rich.progress.track'''
from rich.progress import Progress, MofNCompleteColumn, SpinnerColumn, TimeElapsedColumn, Union, Iterable, ProgressType, Sequence, length_hint


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

		for value in sequence:
			yield value
			self.progress.advance(task_id, 1)
			self.progress.refresh()

		# hide the task after done if it's transient
		if transient:
			self.progress.remove_task(task_id)
