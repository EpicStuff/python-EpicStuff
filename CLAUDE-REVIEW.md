# Claude review

Code review notes. Severity: 🔴 bug that bites in normal use · 🟡 footgun / sharp edge · ⚪ note.

## stuff.py

### 🔴 `Pointer.__getattr__` bypassed the target's own `__getattr__` — FIXED

The fallthrough used `self._t.__getattribute__(attr)`, the *normal* lookup path,
which does **not** fire the target's `__getattr__` on failure (only the `obj.attr`
syntax / `getattr()` does). So any attribute the target served dynamically was
invisible through the Pointer:

```python
Dyn().foo            # 'dynamic:foo'
Pointer(Dyn()).foo   # was: AttributeError 'Dyn' object has no attribute 'foo'
```

Ironic given `NewDict`/`Box` serve keys via `__getattr__`, so `Pointer(some_dict).key`
broke. Fixed by switching the fallthrough to `getattr(self._t, attr)`. The
rich/debugger probe branch (`__rich_repr__`, `_fields`, …) was intentionally left on
`__getattribute__` — it carries the `# @IgnoreException` pragma so the debugger does
not pause on those known-noisy probes, a behavioural difference from the plain
`getattr` path, so it is *not* dead code.

### 🔴 `Tee` / `stdtee` raised `ValueError: I/O operation on closed file` at shutdown — FIXED

`stdtee()` opened the log file, did `atexit.register(file.close)`, and installed the
Tee as `sys.stdout`/`sys.stderr`. At interpreter shutdown the file-close and the
final flush of `sys.stdout` were uncoordinated: the atexit handler closed the file,
then the interpreter flushed `sys.stdout` (the Tee) and finalized the Tee object
(an `io.IOBase`), both of which called `Tee.flush()` → `stream.flush()` on the
already-closed file. Result: a shutdown traceback and exit code 120.

Fixed by making the Tee own the files it opens: it records them in `self._owned`,
drops the `atexit.register`, and overrides `close()` to flush then close only the
owned streams (never the borrowed `sys.stdout`). `write`/`flush` now skip any
already-closed stream (`if not getattr(stream, 'closed', False)`), so the
interpreter's final flush/finalize is a no-op instead of a crash. Repro now exits 0
with the log intact.

Still worth considering later: a context-manager form of `stdtee` that restores the
original `sys.stdout`/`stderr` on exit.

### 🟡 `rmap` mutates its input in place

When the input is mutable and `_list`/`_dict` are not passed, `rmap` mutates the
argument and returns the same object:

```python
orig = {'a': [1, 2]}
out = rmap(orig, lambda v: v * 10)
out is orig          # True  -> orig is now {'a': [10, 20]}
```

Intentional per the inline comments, but surprising for a `map`-named function, and
the opt-out (`_list=`/`_dict=`) is not discoverable. At minimum document it in the
docstring. Logic is otherwise sound: `set`/`frozenset` rebuild correctly, key-only
and val-only modes both work, and `str` is correctly treated as a leaf (not recursed
character-by-character).

### 🟡 `Pointer` proxies only attribute access + call, not dunders

`len(p)`, `p[0]`, `iter(p)`, `repr(p)` hit the `Pointer` itself, because dunders are
resolved on the *type*, not via `__getattr__`:

```python
len(Pointer([1, 2, 3]))   # TypeError: object of type 'Pointer' has no len()
repr(Pointer(5))          # '<...Pointer object at 0x...>'
```

This is exactly what `wrapt.ObjectProxy` solves — already on the README TODO. If
Pointer is meant as a general proxy, adopt it; if it is only for `x._t = …`
attribute rebinding, document the limitation.

### ⚪ Minor

- `open`, `call`/`acall` are clean; `acall` correctly awaits only awaitables.
- `Tee.write` flushes every stream on every write — fine for a redirect, a cost only
  if used on a hot path (not its use case).
- `stdtee` points both stdout *and* stderr at one Tee built from the original
  `sys.stdout` (so stderr loses its own stream) and never restores it — intentional
  but undocumented.
