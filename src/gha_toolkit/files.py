"""The runner-file seam: the five `GITHUB_*`-addressed files a step can write to.

Every workflow command that isn't a stdout `::name ...::message` line goes
through a file the runner points at with an environment variable: `GITHUB_ENV`
for environment exports, `GITHUB_OUTPUT` for step outputs, `GITHUB_STATE` for
action state, `GITHUB_PATH` for `PATH` prepends, and `GITHUB_STEP_SUMMARY` for
the job summary. This module defines that hierarchy: :class:`ActionsFile`, the
shared base; :class:`KeyValueFile`, :class:`PathFile`, and :class:`StepSummaryFile`,
its three concrete shapes; and :class:`ActionsFiles`, the resolved bundle of all
five that a runtime hands to its services.

Ported from ``.original/toolkit/packages/core/src/file-command.ts`` (the
`GITHUB_ENV` / `GITHUB_OUTPUT` / `GITHUB_STATE` heredoc protocol and the
`GITHUB_PATH` line protocol) and ``.original/toolkit/packages/core/src/summary.ts``
(the `GITHUB_STEP_SUMMARY` file, minus its fluent buffer -- the buffer is
:class:`gha_toolkit.summary.ActionSummary`, a later task; this module only owns
the file underneath it).

Deviation of record: upstream's legacy `::set-env` / `::set-output` stdout
fallback for a missing file command was removed from the runner in 2022 and is
not ported here. A missing `GITHUB_ENV` / `GITHUB_OUTPUT` / `GITHUB_STATE` /
`GITHUB_PATH` always raises
:class:`gha_toolkit.exceptions.MissingRunnerFileError` -- there is no stdout
fallback anywhere in this module.

This is an interface-only module: every behavior method below raises
``NotImplementedError``. :class:`ActionsFile` owns `read()` / `update()`;
its three subclasses inherit both unchanged and add their own domain-specific
methods on top, rather than redeclaring the two they inherit. Only
constructors (which store their arguments; no I/O happens at construction
time for any class here) are real.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Generic, TypeVar

from gha_toolkit.commands import OutputValue
from gha_toolkit.environment import GithubEnvironment

FileContentT = TypeVar('FileContentT')
FileContentT.__doc__ = """Type parameter for :class:`ActionsFile`'s `read()` return shape.

Each concrete subclass fixes this to its own domain representation:
`Mapping[str, str]` for :class:`KeyValueFile`, `Sequence[str]` for
:class:`PathFile`, `str` for :class:`StepSummaryFile`.
"""


def _default_delimiter_factory() -> str:
    """Generate a fresh `'ghadelimiter_<uuid4>'` heredoc boundary token.

    Parity with upstream `prepareKeyValueMessage`'s
    ``` `ghadelimiter_${crypto.randomUUID()}` ```. This is
    :class:`KeyValueFile`'s default `delimiter_factory`; tests inject their own
    frozen or counting factories (see `tests/fixtures/runtime.py`) instead of
    relying on this one, so its randomness never leaks into an assertion.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


class ActionsFile(Generic[FileContentT]):
    """Shared seam for the five environment-variable-addressed runner files.

    Owns the two operations every runner file supports: :meth:`read`, which
    parses the file's contents into `FileContentT` -- the domain
    representation each subclass fixes the type parameter to -- and
    :meth:`update`, which appends (or, with `overwrite=True`, replaces) the
    file's raw contents. Concrete subclasses inherit both unchanged and build
    their public API -- `set`, `merge`, `add`, `write`, `clear` -- on top of
    these two primitives; none of them redeclare `read` or `update`.

    `ActionsFile` itself is never the right type to hold a runner file, since
    it does not know how to parse or frame domain data for the wire -- only
    its subclasses (:class:`KeyValueFile`, :class:`PathFile`,
    :class:`StepSummaryFile`) are meant to be constructed. Nothing at runtime
    currently enforces that; it is a design intent, not an `abc.abstractmethod`
    constraint, so that every subclass can inherit :meth:`read` / :meth:`update`
    as-is without each one needing its own `@override`-annotated redeclaration.
    """

    def __init__(self, env_var: str, environment: GithubEnvironment) -> None:
        """Bind this file to the runner-provided `env_var`, resolved via `environment`.

        No filesystem or environment access happens here -- resolving `env_var`
        to a path (and raising
        :class:`gha_toolkit.exceptions.MissingRunnerFileError` if it is unset)
        happens lazily inside :meth:`read` / :meth:`update`, so constructing an
        `ActionsFile` subclass never itself raises.
        """
        self._env_var = env_var
        self._environment = environment

    def read(self) -> FileContentT:
        """Read and parse the bound file into its domain representation.

        Raises:
            gha_toolkit.exceptions.MissingRunnerFileError: `env_var` is unset or
                empty in `environment`, or the path it names does not exist on
                disk. :class:`StepSummaryFile` overrides this contract; see its
                class docstring.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def update(self, content: str, *, overwrite: bool = False) -> None:
        """Append `content` to the bound file, or replace it if `overwrite`.

        Every write is UTF-8 and, when appending, is followed by `os.linesep`
        -- parity with upstream's `fs.appendFileSync(path, content + EOL)`.

        Raises:
            gha_toolkit.exceptions.MissingRunnerFileError: `env_var` is unset or
                empty in `environment`, or the path it names does not exist on
                disk. :class:`StepSummaryFile` overrides this contract; see its
                class docstring.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class KeyValueFile(ActionsFile[Mapping[str, str]]):
    """The `GITHUB_ENV` / `GITHUB_OUTPUT` / `GITHUB_STATE` heredoc protocol.

    Each entry is written as a delimiter-framed heredoc block --
    `'{key}<<{delimiter}\\n{value}\\n{delimiter}'` -- rather than a plain
    `key=value` line, so that a value containing embedded newlines round-trips
    safely. `delimiter` is generated fresh per write by `delimiter_factory`, an
    injectable `Callable[[], str]` (default: :func:`_default_delimiter_factory`,
    a uuid4-based generator); tests substitute frozen or counting factories so
    assertions don't depend on random UUIDs.

    Inherits :meth:`ActionsFile.read` (parses the heredoc blocks into a
    `key -> value` mapping) and :meth:`ActionsFile.update` unchanged; adds
    :meth:`set`, :meth:`__setitem__`, and :meth:`merge` on top.
    """

    def __init__(
        self,
        env_var: str,
        environment: GithubEnvironment,
        delimiter_factory: Callable[[], str] = _default_delimiter_factory,
    ) -> None:
        """Bind this file as :class:`ActionsFile` does, plus a `delimiter_factory`.

        Storing `delimiter_factory` is the only addition over the base
        constructor; it is not called until :meth:`set` (or :meth:`merge`,
        which calls `set`) needs a fresh delimiter.
        """
        super().__init__(env_var, environment)
        self._delimiter_factory = delimiter_factory

    def set(self, key: str, value: OutputValue) -> None:
        """Append one `key`/`value` pair as a delimiter-framed heredoc block.

        Builds the block with a fresh delimiter from `delimiter_factory()`, then
        calls :meth:`update` with the rendered block. Parity with upstream
        `prepareKeyValueMessage` -- see :func:`_default_delimiter_factory`.

        Raises:
            gha_toolkit.exceptions.DelimiterInjectionError: `key`, or `value`
                after `to_command_value` conversion, contains the generated
                delimiter.
            gha_toolkit.exceptions.MissingRunnerFileError: see
                :meth:`ActionsFile.update`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def __setitem__(self, key: str, value: OutputValue) -> None:
        """Alias for `set(key, value)`, enabling `file[key] = value` syntax.

        Raises:
            gha_toolkit.exceptions.DelimiterInjectionError: see :meth:`set`.
            gha_toolkit.exceptions.MissingRunnerFileError: see :meth:`set`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def merge(self, mapping: Mapping[str, OutputValue]) -> None:
        """Call `set(key, value)` for every entry in `mapping`, in order.

        Raises:
            gha_toolkit.exceptions.DelimiterInjectionError: raised by whichever
                entry's `set` call triggers it first; earlier entries in
                `mapping` remain written.
            gha_toolkit.exceptions.MissingRunnerFileError: see :meth:`set`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class PathFile(ActionsFile[Sequence[str]]):
    """The `GITHUB_PATH` protocol: one raw path per line, no heredoc framing.

    Unlike :class:`KeyValueFile`, `GITHUB_PATH` is a plain line-per-entry file
    -- `addPath` upstream appends the raw path plus `EOL`, nothing more -- so
    this class fixes :meth:`ActionsFile.read`'s `FileContentT` to an ordered
    list of lines, not a mapping.

    Inherits :meth:`ActionsFile.read` and :meth:`ActionsFile.update` unchanged;
    adds :meth:`add` on top.
    """

    def add(self, path: str) -> None:
        """Append `path` plus `os.linesep` to the bound file.

        Parity with upstream `addPath` -- no heredoc framing, no delimiter,
        just the raw path.

        Raises:
            gha_toolkit.exceptions.MissingRunnerFileError: see
                :meth:`ActionsFile.update`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class StepSummaryFile(ActionsFile[str]):
    """The `GITHUB_STEP_SUMMARY` file underneath the job summary buffer.

    Deviation from :class:`KeyValueFile` / :class:`PathFile`: a missing or
    inaccessible summary file raises
    :class:`gha_toolkit.exceptions.SummaryAccessError`, not
    :class:`gha_toolkit.exceptions.MissingRunnerFileError` -- parity with
    upstream `summary.ts`, which gives the job summary its own dedicated error
    wording (`"Unable to find environment variable for $GITHUB_STEP_SUMMARY..."`,
    `"Unable to access summary file: ..."`) distinct from the generic file-command
    errors. See :class:`ActionsFiles` for where `MissingRunnerFileError` still
    applies to this file's `env_var`.

    This class owns only the file: writing bytes, in append-or-overwrite mode,
    and truncating to empty. The fluent buffer callers build content with --
    `add_heading`, `add_table`, and so on -- is
    `gha_toolkit.summary.ActionSummary`, a later task; that buffer's `write()`
    hands its accumulated string to this class's :meth:`write`.
    """

    def read(self) -> str:  # ty: ignore[missing-override-decorator]
        """Return the bound file's raw contents.

        Overrides :meth:`ActionsFile.read`'s error contract: this raises
        `SummaryAccessError`, not `MissingRunnerFileError` -- see the class
        docstring for why. (No `@override` decorator: `typing.override` is
        3.12+ and `typing_extensions` is not a dependency of this
        zero-dependency package; the override is real, just undeclared to the
        type checker, which is told about it explicitly via the inline
        `ty: ignore` instead.)

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: `GITHUB_STEP_SUMMARY` is
                unset, or the file it names is not readable.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def update(self, content: str, *, overwrite: bool = False) -> None:  # ty: ignore[missing-override-decorator]
        """Overrides :meth:`ActionsFile.update`'s error contract; delegated to by :meth:`write`.

        See :meth:`read` for why this has no `@override` decorator.

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: `GITHUB_STEP_SUMMARY` is
                unset, or the file it names is not writable.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def write(self, content: str, *, overwrite: bool = False) -> None:
        """Write `content` to the summary file: append by default, truncate first if `overwrite`.

        Parity with upstream `Summary.write` (`options?.overwrite`, defaulting
        to append).

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: `GITHUB_STEP_SUMMARY` is
                unset, or the file it names is not accessible for read/write.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def clear(self) -> None:
        """Truncate the summary file to empty.

        Parity with upstream `Summary.clear`, i.e. `write('', overwrite=True)`.

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: see :meth:`write`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class ActionsFiles:
    """The resolved bundle of all five `GITHUB_*` runner files for a step.

    Exposes `env` and `output` and `state` as :class:`KeyValueFile`, `path` as
    :class:`PathFile`, and `step_summary` as :class:`StepSummaryFile` -- the
    complete set of file-based transports a runtime composes its services on
    top of.

    Resolving this bundle (see :meth:`from_environment`) requires all five
    runner-provided variables -- `GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_STATE`,
    `GITHUB_PATH`, and `GITHUB_STEP_SUMMARY` -- to be present; absence of any of
    them, including `GITHUB_STEP_SUMMARY`, raises
    :class:`gha_toolkit.exceptions.MissingRunnerFileError` uniformly at resolve
    time, because at that point all five are simply "a runner file this step
    needs that the runner did not provide." Once resolved, `env` / `output` /
    `state` / `path` continue to raise `MissingRunnerFileError` for later
    access-time failures (for example the underlying file having been removed
    after resolution), while `step_summary` switches to
    :class:`gha_toolkit.exceptions.SummaryAccessError` for its own operations --
    see :class:`StepSummaryFile` for why. There is no stdout fallback for any of
    the five files, at either layer.
    """

    def __init__(
        self,
        env: KeyValueFile,
        output: KeyValueFile,
        state: KeyValueFile,
        path: PathFile,
        step_summary: StepSummaryFile,
    ) -> None:
        """Store the five already-constructed file handles.

        This is a five-field assignment, no I/O; callers ordinarily reach this
        via :meth:`from_environment` rather than constructing the five handles
        themselves.
        """
        self.env = env
        self.output = output
        self.state = state
        self.path = path
        self.step_summary = step_summary

    @classmethod
    def from_environment(cls, environment: GithubEnvironment) -> 'ActionsFiles':
        """Resolve `GITHUB_ENV` / `OUTPUT` / `STATE` / `PATH` / `STEP_SUMMARY` into an `ActionsFiles`.

        Raises:
            gha_toolkit.exceptions.MissingRunnerFileError: any of the five
                variables is unset or empty in `environment`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
