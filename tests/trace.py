import asyncio

from epicstuff import rich_try, run_install_trace, show_locals

# show_local(True)

local_var = 123

# raise Exception('This is a test error')


@rich_try
def func():
	local_var = 456
	raise ValueError('This is test error 1')


func()

@rich_try(_return='default value', show_locals=False)
async def func2():
	local_var = 789
	raise ValueError('This is test error 2')
asyncio.run(func2())

with rich_try():
	local_var = 999
	show_locals(False)
	raise ValueError('This is test error 3')

# @rich_trace(_raise=False, show_locals=True)
# def func():
# 	raise ValueError('This is a test error')


# @rich_except(show_locals=True)
# def func3():
# 	raise ValueError('This is a test error')


# func3()
