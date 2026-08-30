"""The one generic env binder, and its three faces.

This module defines :func:`bind`: a single generic mechanism that populates a
dataclass instance's fields from a flat `Mapping[str, str]`. Every
environment-shaped binding elsewhere in this package is a face built on top
of this one primitive, rather than its own bespoke parsing logic:

- :func:`get_context` -- binds `gha_toolkit.context.GitHubContext` from the
  process environment's `GITHUB_*` runner variables (stripped of their
  prefix; see `gha_toolkit.context`'s module docstring), plus the separately
  loaded `event` field.
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
T.__doc__ = """Type parameter for the dataclass :func:`bind` populates and returns.

Fixed by whatever dataclass type the caller passes as `model_type` to `bind`
or `get_inputs`.
"""


@dataclasses.dataclass(frozen=True, slots=True)
class EnvVar:
    """`Annotated` metadata marker binding one dataclass field to one environment variable.

    Attach as `Annotated[FieldType, EnvVar('SOME_VAR')]` on a field passed to
    `bind`, when that field needs a source key other than the plain
    convention `bind` otherwise applies (the field's own name, upper-cased,
    looked up directly in the mapping `bind` receives -- see `bind`'s
    docstring). `name` is looked up verbatim, with no case-folding or prefix
    applied. `default` is used when `name` is absent from the mapping,
    taking precedence over the field's own dataclass default when both are
    given.
    """

    name: str
    default: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Input(Generic[T]):
    """`Annotated` metadata marker binding one dataclass field to one `with:` workflow input.

    Attach as `Annotated[FieldType, Input(name='my input', parser=int,
    required=True)]` on a field of a dataclass passed to `get_inputs`.
    Mirrors `gha_toolkit.inputs.ActionsInputs.get`'s contract exactly, since
    `get_inputs` is the dataclass-shaped counterpart to that seam:

    - `name` defaults to the Python field name (with underscores treated as
      spaces) when omitted, then is normalized the same way `ActionsInputs.
      get` resolves a raw input's environment variable: `INPUT_{name.replace(
      ' ', '_').upper()}`.
    - `parser` converts the resolved raw string, defaulting to a `str`
      passthrough when omitted.
    - `required`, when `True`, makes an empty resolved raw value raise
      `gha_toolkit.exceptions.MissingInputError` -- the same exception
      `ActionsInputs.get` raises for the same condition.
    - `default` supplies the field's value when the resolved raw input is
      empty and `required` is `False`, in place of calling `parser` on the
      empty string.
    """

    name: str | None = None
    parser: Callable[[str], T] | None = None
    required: bool = False
    default: T | None = None


def bind(model_type: type[T], mapping: Mapping[str, str]) -> T:
    """Construct a `model_type` instance by binding its fields from `mapping`.

    The one generic mechanism every face of this module is built on. For
    each field of `model_type`, in declaration order (documented resolution
    rule for the future implementation; not yet enforced):

    1. If the field's type is `Annotated[FieldType, EnvVar(name, default)]`,
       resolve `mapping[name]`, falling back to `EnvVar.default`, then to the
       field's own dataclass default if `EnvVar.default` is also `None`.
    2. If the field's type is `Annotated[FieldType, Input(...)]`, resolve
       `mapping[key]` where `key` is `Input`'s normalized `INPUT_*` name (see
       `Input`'s docstring), apply `Input.parser`, and honor `Input.required`
       / `Input.default` per that same docstring.
    3. Otherwise (no marker), resolve `mapping[field.name.upper()]`, falling
       back to the field's own dataclass default if that key is absent. This
       is the convention `get_context` relies on exclusively: it strips the
       `GITHUB_` prefix from every key of the mapping it passes here, so
       `GITHUB_EVENT_NAME` becomes the lookup key `EVENT_NAME`, matching
       `gha_toolkit.context.GitHubContext`'s `event_name` field.
    4. `int`-typed fields (e.g. `GitHubContext.run_attempt`) have their
       resolved string value converted with `int(...)`, parity with upstream
       `parseInt(value, 10)` (`context.ts:48-50`).

    One field is always exempt from this per-field loop: `GitHubContext.
    event`, which `get_context` populates directly (see that function's
    docstring) since it has no single scalar source key.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_context(environ: Mapping[str, str] | None = None) -> GitHubContext:
    """Build a `gha_toolkit.context.GitHubContext` by binding `environ`.

    `environ` defaults to `os.environ` when omitted. Every field except
    `event` is resolved by `bind(GitHubContext, stripped_environ)`, where
    `stripped_environ` is `environ` with every key's `GITHUB_` prefix
    removed (see `bind`'s docstring, rule 3, and `gha_toolkit.context`'s
    module docstring for the naming convention this relies on). `event` is
    populated separately: `gha_toolkit.events.WebhookEvent(event_name=
    environ['GITHUB_EVENT_NAME'], payload=gha_toolkit.events.load_payload(
    environ))`. Parity target: upstream `Context`'s constructor
    (`context.ts:29-55`).

    Raises:
        gha_toolkit.exceptions.EventPayloadError: see
            `gha_toolkit.events.load_payload`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_inputs(model_type: type[T], environ: Mapping[str, str] | None = None) -> T:
    """Build a `model_type` instance from `INPUT_*` entries in `environ`.

    `environ` defaults to `os.environ` when omitted. Delegates to
    `bind(model_type, environ)`; every field of `model_type` is expected to
    carry an `Input` marker (see `Input`) rather than an `EnvVar` marker or
    no marker, since input names are resolved with the `INPUT_*` normalization
    rule documented on `Input`, not looked up verbatim or via `bind`'s plain
    upper-cased-field-name convention.

    Raises:
        gha_toolkit.exceptions.MissingInputError: a field's `Input.required`
            is `True` and its resolved raw value is empty; see
            `gha_toolkit.inputs.ActionsInputs.get`.
        gha_toolkit.exceptions.InputParseError: a field's `Input.parser`
            raises on the resolved raw value.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError
