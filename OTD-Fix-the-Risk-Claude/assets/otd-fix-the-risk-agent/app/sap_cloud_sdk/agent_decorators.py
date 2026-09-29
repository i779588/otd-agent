"""Shim for `sap_cloud_sdk.agent_decorators`.

On the SAP runtime these decorators registered getter functions as
externally-tunable agent configuration (surfaced in the SAP agent-config UI), while
still returning the underlying value when called. Off-platform there is no config
UI, so they are transparent pass-throughs: the decorated getter keeps its behaviour
(e.g. `get_model_name()` still returns its string), and the registration metadata
(key/label/description/validation) is accepted and ignored.

The corresponding configuration is instead driven by environment variables in
app/agent.py (see `.env.example`).
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _passthrough(*_args: Any, **_kwargs: Any) -> Callable[[F], F]:
    """Return a decorator that returns the wrapped function unchanged."""
    def decorator(func: F) -> F:
        return func
    return decorator


def agent_model(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Pass-through: originally registered a tunable model-selection config."""
    return _passthrough(*args, **kwargs)


def agent_config(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Pass-through: originally registered a tunable scalar/string config."""
    return _passthrough(*args, **kwargs)


def prompt_section(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Pass-through: originally registered an editable prompt section."""
    return _passthrough(*args, **kwargs)


__all__ = ["agent_model", "agent_config", "prompt_section"]
