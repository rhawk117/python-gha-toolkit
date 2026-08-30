"""The workflow-input seam: `INPUT_*` environment variables as typed values.

The runner exposes each `with:` entry of a step as an `INPUT_{NAME}` environment
variable, always a raw string. This module defines the single extension point
every typed accessor is built on: :meth:`ActionsInputs.get`, which takes a
caller-supplied ``parser: Callable[[str], T]`` and applies it to the resolved raw
string. The stock accessors (:meth:`ActionsInputs.get_string`,
:meth:`ActionsInputs.get_boolean`, :meth:`ActionsInputs.get_multiline`) are
convenience wrappers over that same primitive, not a separate code path -- a
caller needing a shape none of them cover (an int, a JSON payload, a custom enum)
reaches for :meth:`ActionsInputs.get` directly with their own parser instead of
this module growing a new accessor per shape.

Ported from ``.original/toolkit/packages/core/src/core.ts``'s `getInput` /
`getMultilineInput` / `getBooleanInput` (core.ts:151-208). Deviation of record:
upstream's `getBooleanInput` raises a bare `TypeError` for a value outside the
YAML 1.2 boolean literal set; every parsing failure in this module -- including
that one, and any failure raised by a caller's own ``parser`` passed to
:meth:`ActionsInputs.get` -- raises the typed
:class:`gha_toolkit.exceptions.InputParseError` instead.

This is an interface-only module: every behavior method on
:class:`EnvInputs`, the minimal concrete stub for the :class:`ActionsInputs`
protocol, raises ``NotImplementedError``.
"""

import dataclasses
from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar, runtime_checkable

from gha_toolkit.environment import GithubEnvironment

T = TypeVar('T')


@runtime_checkable
class ActionsInputs(Protocol):
    def get(
        self,
        name: str,
        parser: Callable[[str], T],
        *,
        required: bool = False,
        trim: bool = True,
    ) -> T: ...

    def get_string(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> str: ...

    def get_boolean(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> bool: ...

    def get_multiline(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> Sequence[str]: ...


@dataclasses.dataclass(slots=True)
class EnvInputs:
    environment: GithubEnvironment

    def get(
        self,
        name: str,
        parser: Callable[[str], T],
        *,
        required: bool = False,
        trim: bool = True,
    ) -> T:
        raise NotImplementedError

    def get_string(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> str:
        raise NotImplementedError

    def get_boolean(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> bool:
        raise NotImplementedError

    def get_multiline(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> Sequence[str]:
        raise NotImplementedError
