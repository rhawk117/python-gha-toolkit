"""The runner-file seam: the five `GITHUB_*`-addressed files a step can write to.

Every workflow command that isn't a stdout `::name ...::message` line goes
through a file the runner points at with an environment variable: `GITHUB_ENV`
for environment exports, `GITHUB_OUTPUT` for step outputs, `GITHUB_STATE` for
action state, `GITHUB_PATH` for `PATH` prepends, and `GITHUB_STEP_SUMMARY` for
the job summary. This module defines that hierarchy as protocols:
:class:`ActionsFile`, the shared generic base; :class:`KeyValueFile`,
:class:`PathFile`, and :class:`StepSummaryFile`, its three shapes. Their
minimal concrete stubs are :class:`HeredocFile`, :class:`PathListFile`, and
:class:`SummaryFile` respectively. :class:`RunnerFiles` is the resolved
bundle of all five that a runtime hands to its services; its five fields are
built and passed in directly by `gha_toolkit.runtime.create_runtime`, the
composition root, from a bound
:class:`gha_toolkit.environment.GithubEnvironment`.

Ported from ``.original/toolkit/packages/core/src/file-command.ts`` (the
`GITHUB_ENV` / `GITHUB_OUTPUT` / `GITHUB_STATE` heredoc protocol and the
`GITHUB_PATH` line protocol) and ``.original/toolkit/packages/core/src/summary.ts``
(the `GITHUB_STEP_SUMMARY` file, minus its fluent buffer -- the buffer is
:class:`gha_toolkit.summary.ActionSummary`; this module only owns the file
underneath it).

Deviation of record: upstream's legacy `::set-env` / `::set-output` stdout
fallback for a missing file command was removed from the runner in 2022 and is
not ported here. A missing `GITHUB_ENV` / `GITHUB_OUTPUT` / `GITHUB_STATE` /
`GITHUB_PATH` always raises
:class:`gha_toolkit.exceptions.MissingRunnerFileError` -- there is no stdout
fallback anywhere in this module.

This is an interface-only module: every behavior method on the concrete
stubs raises ``NotImplementedError``. `ActionsFile`, `KeyValueFile`,
`PathFile`, and `StepSummaryFile` are protocols -- there is no behavior to
implement, only shape to satisfy.
"""

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from typing import Protocol, TypeVar, runtime_checkable

from gha_toolkit.commands import OutputValue
from gha_toolkit.environment import GithubEnvironment

FileContentT_co = TypeVar('FileContentT_co', covariant=True)


def _default_delimiter_factory() -> str:
    raise NotImplementedError


@runtime_checkable
class ActionsFile(Protocol[FileContentT_co]):
    def read(self) -> FileContentT_co: ...

    def update(self, content: str, *, overwrite: bool = False) -> None: ...


@runtime_checkable
class KeyValueFile(ActionsFile[Mapping[str, str]], Protocol):
    def set(self, key: str, value: OutputValue) -> None: ...


@runtime_checkable
class PathFile(ActionsFile[Sequence[str]], Protocol):
    def add(self, path: str) -> None: ...


@runtime_checkable
class StepSummaryFile(ActionsFile[str], Protocol):
    def clear(self) -> None: ...


@dataclasses.dataclass(slots=True)
class HeredocFile:
    env_var: str
    environment: GithubEnvironment
    delimiter_factory: Callable[[], str] = _default_delimiter_factory

    def read(self) -> Mapping[str, str]:
        raise NotImplementedError

    def update(self, content: str, *, overwrite: bool = False) -> None:
        raise NotImplementedError

    def set(self, key: str, value: OutputValue) -> None:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class PathListFile:
    env_var: str
    environment: GithubEnvironment

    def read(self) -> Sequence[str]:
        raise NotImplementedError

    def update(self, content: str, *, overwrite: bool = False) -> None:
        raise NotImplementedError

    def add(self, path: str) -> None:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class SummaryFile:
    env_var: str
    environment: GithubEnvironment

    def read(self) -> str:
        raise NotImplementedError

    def update(self, content: str, *, overwrite: bool = False) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class RunnerFiles:
    env: KeyValueFile
    output: KeyValueFile
    state: KeyValueFile
    path: PathFile
    step_summary: StepSummaryFile
