"""The one generic env binder, and its three faces.

This module defines :func:`bind`: a single generic mechanism that populates a
dataclass instance's fields from a flat `Mapping[str, str]`. Every
environment-shaped binding elsewhere in this package is a face built on top
of this one primitive, rather than its own bespoke parsing logic:

- :func:`get_context` -- binds `gha_toolkit.context.GitHubContext` from the
  process environment's `GITHUB_*` runner variables (stripped of their
  prefix; see `gha_toolkit.context`'s module docstring), plus the separately
  loaded `event` field. `run_attempt`, `run_number`, and `run_id` -- the
  three `int`-typed fields -- are parsed as `int` from their string
  environment values. `api_url`, `server_url`, and `graphql_url` fall back
  to `GitHubContext`'s declared defaults (`https://api.github.com`,
  `https://github.com`, `https://api.github.com/graphql`) when their
  runner variables are unset, rather than raising. `event` has no
  runner-variable counterpart: it is populated separately, by loading and
  parsing `GITHUB_EVENT_PATH`'s JSON payload into a
  `gha_toolkit.events.WebhookEvent`, not by :func:`bind`.
- :func:`get_inputs` -- binds a caller-supplied dataclass from the process
  environment's `INPUT_*` step-input variables, per field :class:`Input`
  metadata -- the dataclass-shaped counterpart to
  `gha_toolkit.inputs.ActionsInputs.get` for callers who want a whole set of
  named inputs bound onto one typed object in a single call.
- `gha_toolkit.events.WebhookEvent.unwrap` -- binds a webhook's JSON payload
  onto a hand-written or generated event-model dataclass. This third
  consumer shares this module's design principle (metadata-driven dataclass
  population from an external mapping) but does not call :func:`bind`
  directly: a webhook payload is `Mapping[str, JsonValue]`, arbitrarily
  nested, not the flat `Mapping[str, str]` :func:`bind`'s signature requires,
  so it implements its own binding logic in `gha_toolkit.events`.

:class:`EnvVar` and :class:`Input` are the two `typing.Annotated` metadata
markers `bind` reads to resolve each field's source key. Both are pure data
(frozen dataclasses, no behavior) and are real, complete definitions.

This is an interface-only module: :func:`bind`, :func:`get_context`, and
:func:`get_inputs` raise ``NotImplementedError``.
"""

import dataclasses
from collections.abc import Callable, Mapping
from typing import Generic, TypeVar

from gha_toolkit.context import GitHubContext

T = TypeVar('T')


@dataclasses.dataclass(frozen=True, slots=True)
class EnvVar:
    name: str
    default: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Input(Generic[T]):
    name: str | None = None
    parser: Callable[[str], T] | None = None
    required: bool = False
    default: T | None = None


def bind(model_type: type[T], mapping: Mapping[str, str]) -> T:
    raise NotImplementedError


def get_context(environ: Mapping[str, str] | None = None) -> GitHubContext:
    raise NotImplementedError


def get_inputs(model_type: type[T], environ: Mapping[str, str] | None = None) -> T:
    raise NotImplementedError
