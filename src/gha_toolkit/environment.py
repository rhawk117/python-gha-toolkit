"""The process-environment seam every other subsystem reads runner state through.

:class:`GithubEnvironment` is the `@runtime_checkable` protocol every other
subsystem in this package depends on instead of reading `os.environ` ad hoc --
binding through one typed seam is what lets tests substitute a fake mapping
instead of monkeypatching the real process environment, and is the single
place a future implementation enforces "no stdout fallback" for missing
runner state. :class:`ProcessEnvironment` is this protocol's minimal concrete
stub, wrapping an injectable `environ` mapping (default: `os.environ`,
resolved lazily via `default_factory` so importing this module never itself
reads process state).

Ported from ``.original/toolkit/packages/core/src/core.ts``'s ``exportVariable`` /
``process.env`` reads scattered across that file; this module consolidates them.
Upstream's ``exportVariable`` also prepends to ``process.env.PATH`` with the
platform path separator as a side effect of setting ``PATH`` specifically -- that
PATH-prepending policy is a services-layer concern (``ActionsPaths``) and does
not belong on this seam, which only binds and writes environment entries.

This is an interface-only module: every method on :class:`ProcessEnvironment`
raises ``NotImplementedError``. `GithubEnvironment` is a protocol -- there is
no behavior to implement, only shape to satisfy.
"""

import dataclasses
import os
from collections.abc import MutableMapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class GithubEnvironment(Protocol):
    def get(self, name: str, default: str | None = None) -> str | None: ...

    def require(self, name: str) -> str: ...

    def set(self, name: str, value: str) -> None: ...


@dataclasses.dataclass(slots=True)
class ProcessEnvironment:
    environ: MutableMapping[str, str] = dataclasses.field(
        default_factory=lambda: os.environ
    )

    def get(self, name: str, default: str | None = None) -> str | None:
        raise NotImplementedError

    def require(self, name: str) -> str:
        raise NotImplementedError

    def set(self, name: str, value: str) -> None:
        raise NotImplementedError
