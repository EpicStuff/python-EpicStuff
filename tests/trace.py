from epicstuff.trace import *

# show_local(True)

local_var = 123

# raise Exception('This is a test error')


# @rich_trace
# def func():
# 	raise ValueError('This is a test error')

@rich_trace(_raise=False, show_locals=True)
def func():
	raise ValueError('This is a test error')

@rich_try
def func2():
	raise ValueError('This is a test error')

@rich_except(show_locals=True)
def func3():
	raise ValueError('This is a test error')


func()
func2()
func3()
