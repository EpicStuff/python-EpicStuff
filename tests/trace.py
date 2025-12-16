import asyncio

from epicstuff import rich_try, run_install_trace, update_trace, rich_trace, Dict

# show_local(True)

local_var = 123

# raise Exception('This is a test error')

@rich_try(locals_max_length=None)
def func():
	local_var = Dict(a=[None] * 50, b=Dict(c=Dict(d=[None] * 50)), e={num: num for num in range(50)})
	raise Exception('make sure local is visible and not truncated')


func()

@rich_try
def func():
	local_var = Dict(a=[None] * 200, b=Dict(c=Dict(d=[None] * 200)), e={num: num for num in range(100)})
	raise Exception('make sure local is visible and truncated')


func()

@rich_try()
def func():
	local_var = Dict(a=[None] * 50, b=Dict(c=Dict(d=[None] * 50)), e={num: num for num in range(50)})
	update_trace(locals_max_length=3)
	raise Exception('make sure local is visible and properly truncated')


func()


@rich_trace(_raise=False)
def func():
	raise ValueError('you should not see this')


func()


@rich_try(_return='default value', show_locals=False)
async def func2():
	local_var = 789
	raise ValueError('test 2: make sure local is not visible')
asyncio.run(func2())

with rich_try():
	local_var = 999
	update_trace(False)
	raise ValueError('test 3: make sure local is not visible')

# @rich_trace(_raise=False, show_locals=True)
# def func():
# 	raise ValueError('This is a test error')


# @rich_except(show_locals=True)
# def func3():
# 	raise ValueError('This is a test error')


# func3()
