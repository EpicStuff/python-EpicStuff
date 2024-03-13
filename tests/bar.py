from rich.progress import Progress

import time

# with Progress() as progress:
# 	task = progress.add_task("task", total=100)
# 	for i in range(100):
# 		sub_task = progress.add_task("subtask", total=100)
# 		for j in range(100):
# 			time.sleep(0.01)  # some task

# 			progress.update(sub_task, advance=1)

# 		progress.remove_task(sub_task)
# 		progress.update(task, advance=1)

from epicstuff import Bar

with Bar() as bar:
	for i in bar(range(100)):
		for j in bar(range(100), transient=True):
			time.sleep(0.01)  # some task
