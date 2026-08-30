"""Typed factory-fixture signatures shared across test modules.

Consolidates the `Callable[..., X]` aliases that were redeclared verbatim in
six `tests/test_*.py` modules -- the `...` erased every argument, so a call
like `make_environment(1, 2, 3)` type-checked. These `Protocol`s spell the
real parameter list of the fixture factory each one stands in for.
"""

from collections.abc import Callable, Mapping
from typing import Protocol

from gha_toolkit.environment import GithubEnvironment, ProcessEnvironment
from gha_toolkit.files import HeredocFile
from gha_toolkit.services import StepOutput, StepState


class MakeEnvironment(Protocol):
    def __call__(
        self, overrides: Mapping[str, str] | None = None
    ) -> ProcessEnvironment: ...


class MakeEnvFile(Protocol):
    def __call__(
        self,
        environment: GithubEnvironment,
        delimiter: Callable[[], str] | None = None,
    ) -> HeredocFile: ...


class MakeOutput(Protocol):
    def __call__(
        self,
        environment: GithubEnvironment,
        delimiter: Callable[[], str] | None = None,
    ) -> StepOutput: ...


class MakeState(Protocol):
    def __call__(
        self,
        environment: GithubEnvironment,
        delimiter: Callable[[], str] | None = None,
    ) -> StepState: ...
