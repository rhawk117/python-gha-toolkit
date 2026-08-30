"""Small service seams built directly on the runner-file and environment seams.

Three services, each a thin domain wrapper over an already-typed transport
from :mod:`gha_toolkit.files` or :mod:`gha_toolkit.environment`:
:class:`ActionsOutput` (step outputs, over a `GITHUB_OUTPUT`-bound
:class:`gha_toolkit.files.KeyValueFile`), :class:`ActionsState` (action
state, over a `GITHUB_STATE`-bound :class:`gha_toolkit.files.KeyValueFile`
for writes and a :class:`gha_toolkit.environment.GithubEnvironment` for
reads), and :class:`ActionsPaths` (`PATH` prepending, over a
`GITHUB_PATH`-bound :class:`gha_toolkit.files.PathFile` for the runner-file
side and a :class:`gha_toolkit.environment.GithubEnvironment` for the live
process `PATH` side).

Ported from ``.original/toolkit/packages/core/src/core.ts``'s `setOutput`
(`core.ts:217-224`), `saveState` (`377-384`), `getState` (`386-393`), and the
`GITHUB_PATH`-branch of `addPath` (`132-139`) -- minus each function's legacy
stdout-command fallback for a missing runner file, which
`gha_toolkit.files` already removed at the transport layer (see that
module's docstring).

This is an interface-only module: every behavior method below raises
``NotImplementedError``. Only the three constructors, which store their
arguments, are real.
"""

from gha_toolkit.commands import OutputValue
from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import KeyValueFile, PathFile


class ActionsOutput:
    """Sets a step's `GITHUB_OUTPUT` entries.

    A thin wrapper over an `GITHUB_OUTPUT`-bound
    :class:`gha_toolkit.files.KeyValueFile`; this class exists so callers
    depend on a domain-named service (`ActionsOutput`) rather than on the
    generic `KeyValueFile` transport directly.
    """

    def __init__(self, output_file: KeyValueFile) -> None:
        """Bind this instance to `output_file`.

        Storing the reference is the entire constructor; no write happens
        until :meth:`set` is called.
        """
        self._output_file = output_file

    def set(self, name: str, value: OutputValue) -> None:
        """Set the step output `name` to `value`.

        Parity with upstream `setOutput` (`core.ts:217-224`), minus its
        legacy stdout-command fallback: delegates to the bound
        `KeyValueFile`'s `set(name, value)`, which appends a delimiter-framed
        heredoc block to the file `GITHUB_OUTPUT` names.

        Raises:
            gha_toolkit.exceptions.DelimiterInjectionError: see
                :meth:`gha_toolkit.files.KeyValueFile.set`.
            gha_toolkit.exceptions.MissingRunnerFileError: see
                :meth:`gha_toolkit.files.KeyValueFile.set`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class ActionsState:
    """Saves and reads an action's own `GITHUB_STATE` entries.

    State set during a step's main execution is only readable by that same
    action's own post-job execution -- upstream's contract, unchanged here.
    Writes go through a `GITHUB_STATE`-bound
    :class:`gha_toolkit.files.KeyValueFile`; reads go through the bound
    :class:`gha_toolkit.environment.GithubEnvironment` instead, since a
    previously-saved state entry surfaces back to the action as a
    `STATE_{name}` environment variable, not by re-reading the file.
    """

    def __init__(
        self, state_file: KeyValueFile, environment: GithubEnvironment
    ) -> None:
        """Bind this instance to `state_file` and `environment`.

        Storing the two references is the entire constructor; no I/O happens
        until :meth:`save` or :meth:`get` is called.
        """
        self._state_file = state_file
        self._environment = environment

    def save(self, name: str, value: OutputValue) -> None:
        """Save state entry `name` as `value` for this action's post-job execution.

        Parity with upstream `saveState` (`core.ts:377-384`), minus its
        legacy stdout-command fallback: delegates to the bound
        `KeyValueFile`'s `set(name, value)`, which appends a delimiter-framed
        heredoc block to the file `GITHUB_STATE` names.

        Raises:
            gha_toolkit.exceptions.DelimiterInjectionError: see
                :meth:`gha_toolkit.files.KeyValueFile.set`.
            gha_toolkit.exceptions.MissingRunnerFileError: see
                :meth:`gha_toolkit.files.KeyValueFile.set`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def get(self, name: str) -> str:
        """Return the value this action previously saved for state entry `name`.

        Parity with upstream `getState` (`core.ts:386-393`,
        `process.env['STATE_' + name] || ''`): reads `STATE_{name}` from the
        bound environment, defaulting to `''` if unset -- there is no
        "required" mode and no typed error for a missing entry, matching
        upstream exactly.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class ActionsPaths:
    """Prepends directories to `PATH`, for this step and every step after it.

    Two effects per call, both required for parity with upstream `addPath`
    (`core.ts:132-139`): the prepended directory is recorded to the
    `GITHUB_PATH`-bound :class:`gha_toolkit.files.PathFile` so the runner
    prepends it to `PATH` for every subsequent step in the job, *and* the
    live process's own `PATH` environment variable (read and written through
    the bound :class:`gha_toolkit.environment.GithubEnvironment`) is updated
    immediately so steps running later in this same process see the change
    too -- upstream's `process.env['PATH'] = `${inputPath}${path.delimiter}${process.env['PATH']}``,
    ported as an `os.pathsep`-joined prepend. This side effect intentionally
    lives here rather than on `GithubEnvironment` itself -- see that module's
    docstring.
    """

    def __init__(self, path_file: PathFile, environment: GithubEnvironment) -> None:
        """Bind this instance to `path_file` and `environment`.

        Storing the two references is the entire constructor; no I/O happens
        until :meth:`add` is called.
        """
        self._path_file = path_file
        self._environment = environment

    def add(self, path: str) -> None:
        """Prepend `path` to `PATH`, for the runner-wide list and this process.

        Parity with upstream `addPath` (`core.ts:132-139`), minus its legacy
        stdout-command fallback for a missing `GITHUB_PATH`: appends `path`
        to the bound `PathFile` (a single raw line, no heredoc framing -- see
        :meth:`gha_toolkit.files.PathFile.add`), then prepends `path` plus
        `os.pathsep` to the live `PATH` value in the bound environment.

        Raises:
            gha_toolkit.exceptions.MissingRunnerFileError: see
                :meth:`gha_toolkit.files.PathFile.add`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
