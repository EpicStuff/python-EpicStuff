import asyncio, contextlib, sys, unittest
from io import StringIO
from typing import IO, NoReturn

from epicstuff import NewDict as Dict, rich_trace, rich_try, trace as _trace, update_trace
from parameterized import parameterized
from rich.console import Console


# When true, rendered tracebacks are echoed to the real terminal in addition to being
# captured for assertions — set in __main__ so a manual run shows the exceptions to eyeball.
visual = False


class _Tee:
	'Write-only text stream fanning writes out to several underlying streams.'

	def __init__(self, *streams: IO[str]) -> None:
		self.streams: tuple[IO[str], ...] = streams
	def write(self, s: str) -> int:
		for stream in self.streams:
			stream.write(s)
		return len(s)
	def flush(self) -> None:
		for stream in self.streams:
			stream.flush()


@contextlib.contextmanager
def capture_trace(width=160):
	'''Swap the rich console for one writing to a StringIO so rendered tracebacks are assertable.

	`console` is a Pointer; redirecting its `._t` reroutes every `console.print(...)` in
	`_RichTrace._handle_exc` into our buffer without touching the public API. The original
	target is restored on exit. When VISUAL is set the buffer is teed to the real stdout so
	the rendered tracebacks are also printed for manual verification.
	'''
	buf = StringIO()
	target = _Tee(buf, sys.stdout) if visual else buf
	old = _trace.console._t
	_trace.console._t = Console(file=target, width=width)  # pyright: ignore[reportArgumentType]  # _Tee duck-types IO[str]
	try:
		yield buf
	finally:
		_trace.console._t = old


class TestTrace(unittest.TestCase):
	def test_rich_try_shows_local_not_truncated(self) -> None:
		'rich_try(locals_max_length=None) prints the traceback with the full local visible, then returns None.'
		with capture_trace() as buf:
			sentinel = str(5 * 111111)  # '555555', built not written -> only appears if the panel renders it
			@rich_try(locals_max_length=None)
			def func() -> NoReturn:
				local_var = Dict(a=[None] * 50, b=Dict(c=Dict(d=[None] * 50)), e={num: num for num in range(50)}, marker=int(sentinel))  # noqa: F841
				raise Exception('make sure local is visible and not truncated')
			result = func()
		out = buf.getvalue()
		self.assertIsNone(result)
		self.assertIn('make sure local is visible and not truncated', out)
		# positive control: the locals panel renders, so the built sentinel value is visible (and not truncated)
		self.assertIn(sentinel, out)

	def test_rich_try_shows_local_truncated(self) -> None:
		'rich_try (default locals_max_length=16) truncates the oversized local when rendering.'
		with capture_trace() as buf:
			@rich_try
			def func() -> NoReturn:
				local_var = Dict(a=[None] * 200, b=Dict(c=Dict(d=[None] * 200)), e={num: num for num in range(100)})  # noqa: F841
				raise Exception('make sure local is visible and truncated')
			result = func()
		out = buf.getvalue()
		self.assertIsNone(result)
		self.assertIn('make sure local is visible and truncated', out)
		self.assertIn('locals', out.lower())
		# 200-element list rendered under a 16-cap must be truncated -> rich emits a "... +N" marker
		self.assertIn('...', out)

	def test_update_trace_truncation_in_flight(self) -> None:
		'update_trace(locals_max_length=3) tightens truncation for the traceback rendered by the same call.'
		try:
			with capture_trace() as buf:
				@rich_try()
				def func() -> NoReturn:
					local_var = Dict(a=[None] * 50, b=Dict(c=Dict(d=[None] * 50)), e={num: num for num in range(50)})  # noqa: F841
					update_trace(locals_max_length=3)
					raise Exception('make sure local is visible and properly truncated')
				result = func()
			out = buf.getvalue()
			self.assertIsNone(result)
			self.assertIn('make sure local is visible and properly truncated', out)
			self.assertIn('locals', out.lower())
			self.assertIn('...', out)
		finally:
			# update_trace mutates module-global _trace_kwargs; restore the default so later tests aren't affected
			update_trace(locals_max_length=16)

	def test_rich_trace_no_raise_is_silent(self) -> None:
		'rich_trace(_raise=False) neither prints nor re-raises, and returns _return (None).'
		with capture_trace() as buf:
			@rich_trace(_raise=False)
			def func() -> NoReturn:
				raise ValueError('you should not see this')
			result = func()
		out = buf.getvalue()
		self.assertIsNone(result)
		self.assertEqual(out.strip(), '')
		self.assertNotIn('you should not see this', out)

	def test_rich_try_async_return_and_hidden_locals(self) -> None:
		'Async rich_try(_return=..., show_locals=False) returns _return and omits locals from the render.'
		# The sentinel is built (not written as a literal) so its digits never appear in the frame's echoed
		# source line -> its presence in `out` means the locals panel rendered, its absence means it did not.
		sentinel = str(6 * 111111)  # '666666'
		with capture_trace() as buf:
			@rich_try(_return='default value', show_locals=False)
			async def func2() -> NoReturn:
				local_var = int(sentinel)  # noqa: F841
				raise ValueError('test 2: make sure local is not visible')
			result = asyncio.run(func2())
		out = buf.getvalue()
		self.assertEqual(result, 'default value')
		self.assertIn('test 2: make sure local is not visible', out)
		# show_locals=False -> no locals panel -> the local's value is not rendered anywhere
		self.assertNotIn(sentinel, out)

	def test_rich_try_context_manager_suppresses(self) -> None:
		'The `with rich_try():` context manager renders the traceback and suppresses the exception.'
		reached_after = False
		sentinel = str(7 * 111111)  # '777777', built not written -> not echoed in the source frame
		try:
			with capture_trace() as buf:
				with rich_try():
					local_var = int(sentinel)  # noqa: F841
					update_trace(False)
					raise ValueError('test 3: make sure local is not visible')
				reached_after = True
			out = buf.getvalue()
			self.assertTrue(reached_after)
			self.assertIn('test 3: make sure local is not visible', out)
			# update_trace(False) turned show_locals off before the raise -> no locals panel -> value absent
			self.assertNotIn(sentinel, out)
		finally:
			# update_trace(False) flipped show_locals off globally; restore the default
			update_trace(True)

	@parameterized.expand([
		# (name, _raise, expected re-raise?, expected return when not raising)
		('raise_true', True, True, None),
		('raise_none_returns', None, False, 'RET'),
		('raise_false_returns', False, False, 'RET'),
	])
	def test_raise_modes(self, name, raise_mode, should_reraise, expected_return) -> None:
		'The _raise flag drives whether _handle_exc re-raises or returns _return; the traceback still prints unless _raise is False.'
		with capture_trace() as buf:
			@rich_trace(_raise=raise_mode, _return='RET')
			def func() -> NoReturn:
				raise RuntimeError('mode marker')
			if should_reraise:
				with self.assertRaises(RuntimeError):
					func()
			else:
				self.assertEqual(func(), expected_return)
		out = buf.getvalue()
		if raise_mode is False:
			# _raise=False stays silent
			self.assertEqual(out.strip(), '')
		else:
			self.assertIn('mode marker', out)


if __name__ == '__main__':
	visual = True  # echo the rendered tracebacks to the terminal for manual inspection
	unittest.TestLoader().loadTestsFromTestCase(TestTrace).debug()
	print('All tests passed')
