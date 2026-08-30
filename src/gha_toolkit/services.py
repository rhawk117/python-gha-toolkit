"""Small service seams built directly on the runner-file and environment seams.

Three service protocols, each a thin domain wrapper over an already-typed
transport from :mod:`gha_toolkit.files` or :mod:`gha_toolkit.environment`:
:class:`ActionsOutput` (step outputs, over a `GITHUB_OUTPUT`-bound
:class:`gha_toolkit.files.KeyValueFile`), :class:`ActionsState` (action
state, over a `GITHUB_STATE`-bound :class:`gha_toolkit.files.KeyValueFile`
for writes and a :class:`gha_toolkit.environment.GithubEnvironment` for
reads), and :class:`ActionsPaths` (`PATH` prepending, over a
`GITHUB_PATH`-bound :class:`gha_toolkit.files.PathFile` for the runner-file
side and a :class:`gha_toolkit.environment.GithubEnvironment` for the live
process `PATH` side). :class:`StepOutput`, :class:`StepState`, and
:class:`RunnerPaths` are their respective minimal concrete stubs.

Ported from ``.original/toolkit/packages/core/src/core.ts``'s `setOutput`
(`core.ts:217-224`), `saveState` (`377-384`), `getState` (`386-393`), and the
`GITHUB_PATH`-branch of `addPath` (`132-139`) -- minus each function's legacy
stdout-command fallback for a missing runner file, which
`gha_toolkit.files` already removed at the transport layer (see that
module's docstring).

This is an interface-only module: every behavior method on the three
concrete stubs raises ``NotImplementedError``. `ActionsOutput`,
`ActionsState`, and `ActionsPaths` are protocols -- there is no behavior to
implement, only shape to satisfy.
"""

import dataclasses
from typing import Protocol, runtime_checkable

from gha_toolkit.commands import OutputValue
from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import KeyValueFile, PathFile


@runtime_checkable
class ActionsOutput(Protocol):
    def set(self, name: str, value: OutputValue) -> None: ...


@runtime_checkable
class ActionsState(Protocol):
    def save(self, name: str, value: OutputValue) -> None: ...

    def get(self, name: str) -> str: ...


@runtime_checkable
class ActionsPaths(Protocol):
    def add(self, path: str) -> None: ...


@dataclasses.dataclass(slots=True)
class StepOutput:
    output_file: KeyValueFile

    def set(self, name: str, value: OutputValue) -> None:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class StepState:
    state_file: KeyValueFile
    environment: GithubEnvironment

    def save(self, name: str, value: OutputValue) -> None:
        raise NotImplementedError

    def get(self, name: str) -> str:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class RunnerPaths:
    path_file: PathFile
    environment: GithubEnvironment

    def add(self, path: str) -> None:
        raise NotImplementedError
