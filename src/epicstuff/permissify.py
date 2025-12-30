import contextlib
from collections.abc import Callable
from functools import wraps
from inspect import Parameter, Signature, signature
from typing import Any, ParamSpec, TypeVar, cast

P = ParamSpec('P')
R = TypeVar('R')


def permissify(func: Callable[P, R], positional_overwrite_defaults: bool = True, keyword_overrides_passed_positional: bool = True) -> Callable[P, R]:  # noqa: UP047
	'''Return a wrapper that accepts and ignores extra *args/**kwargs.

	i think this is almost entirely written by ChatGPT

	Parameters
	----------
	func: Callable
		Original function to wrap.
	positional_overwrite_defaults: bool, default True
		If True, positional arguments provided for parameters with defaults (e.g. ``b=2``) will override those defaults.
		If False, positional arguments beyond those needed to satisfy required (non-default) positional parameters are ignored and the function's default values are used instead.
	keyword_overrides_passed_positional: bool, default True
		If True, a keyword argument overrides a previously supplied positional value for a positional-or-keyword parameter
		If False, positional values are kept and duplicate keywords for those names are ignored.

	Behavior
	--------
	- Required positional parameters (no default) are always consumed.
	- Optional positional-or-keyword parameters (with defaults) are consumed only if ``positional_overwrite_defaults`` is True.
	- Positional-only parameters follow the same required/optional consumption rule; they are never overridden by keywords.
	- Unknown keywords are ignored unless the original function accepts ``**kwargs``.
	- Keyword overriding of consumed positional values depends on ``keyword_overrides_passed_positional``.

	'''
	sig = signature(func)
	params = list(sig.parameters.values())
	# Whether the original function already accepts extra positionals/keywords.
	has_var_pos = any(p.kind is Parameter.VAR_POSITIONAL for p in params)
	has_var_kw = any(p.kind is Parameter.VAR_KEYWORD for p in params)

	# Positional-only and positional-or-keyword params, in order.
	pos_params = [
		p for p in params if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
	]
	# Count how many of those are required (no default).
	required_pos_count = sum(1 for p in pos_params if p.default is Parameter.empty)
	# Names allowed as keywords when the original function doesn't have **kwargs.
	accepted_kw = {p.name for p in params if p.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)}

	@wraps(func)
	def wrapper(*args: Any, **kwargs: Any) -> R:
		# Accept broad args; we trim/override based on the original signature.
		pass_args: list[Any] = []
		fkwargs: dict[str, Any] = {}
		if has_var_pos:
			# Original already takes *args: forward all positionals.
			pass_args = list(args)
			consume = len(pass_args)
		else:
			# Decide how many positional args to consume:
			# - If overwriting defaults, allow filling optional positional slots too.
			# - Otherwise, stop at the required count so defaults are preserved.
			consume = min(
				len(args),
				len(pos_params) if positional_overwrite_defaults else required_pos_count,
			)
			pass_args = list(args[:consume])

		# Optionally allow keywords to override consumed positional-or-keyword values.
		if keyword_overrides_passed_positional:
			for i, p in enumerate(pos_params[:consume]):
				if p.kind is Parameter.POSITIONAL_OR_KEYWORD and p.name in kwargs:
					pass_args[i] = kwargs.pop(p.name)

		# Avoid duplicate named parameters. If the original doesn't accept **kwargs,
		# also drop unknown keyword names.
		filled = {p.name for p in pos_params[:consume]}
		if has_var_kw:
			# Pass all remaining keywords except those already provided positionally.
			fkwargs = {k: v for k, v in kwargs.items() if k not in filled}
		else:
			# Restrict to known keyword-capable names and avoid duplicates.
			fkwargs = {k: v for k, v in kwargs.items() if k in accepted_kw and k not in filled}

		# Call the original function. Casting placates ParamSpec at this call site.
		return cast('Any', func)(*pass_args, **fkwargs)

	# Expose a permissive synthetic signature so introspection and callers
	# see that the wrapper tolerates extra *args/**kwargs.
	# dont think this works
	sig_params = params[:]
	if not has_var_pos:
		sig_params.append(Parameter('_', kind=Parameter.VAR_POSITIONAL))
	if not has_var_kw:
		sig_params.append(Parameter('w_', kind=Parameter.VAR_KEYWORD))
	with contextlib.suppress(Exception):  # pragma: no cover
		wrapper.__signature__ = Signature(parameters=sig_params, return_annotation=sig.return_annotation)  # type: ignore[attr-defined]

	return cast('Callable[P, R]', wrapper)
