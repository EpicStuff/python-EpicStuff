# Review notes

## trace.py

### Terminal width is snapshotted at import time

`_trace_kwargs` bakes `width` from a one-time `_term_width()` call at module import:

```python
_trace_kwargs = Dict({'show_locals': True, 'locals_max_length': 16, 'width': _term_width(), 'suppress': [...]})
```

That integer flows into every `context_kwargs` and is passed explicitly to
`Traceback.from_exception(width=...)`. Verified against rich's source
(`rich/traceback.py`): `Traceback.__rich_console__` pins the render with
`Constrain(stack_renderable, self.width)`, so a set `width` is honored verbatim
and rich does **not** re-measure the terminal per print.

Consequence: if the terminal is resized after import, tracebacks keep rendering
at the import-time width. If the import happened with no TTY, the width is the
`_term_width()` fallback (160) forever.

Note this is *better* than rich's default, not worse: `Traceback.from_exception`
defaults `width=100` (a fixed constant), so omitting `width` would pin every
trace to 100 rather than auto-detecting. The only value that adapts per-render
is `width=None` -> `Constrain(..., None)` imposes no limit and defers to the
console, whose `_width` is `None` (no width in `_console_kwargs`), so
`Console.size` re-measures `os.get_terminal_size()` on each `print`.

Options:
- Keep the import-time snapshot (deliberate, fixed width; stale on resize).
- Pass `width=None` for live per-render adaptation to the current terminal.
- Recompute `_term_width()` inside `update_trace`/`_handle_exc` if a measured
  default is wanted without going fully adaptive.
