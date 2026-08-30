"""The `gha_toolkit.core` module facade: `core.info(...)` is the whole user API.

Every function in this module is a thin wrapper: it resolves the current
`gha_toolkit.runtime.ActionsRuntime` via `gha_toolkit.runtime.current_runtime`
(bound by `gha_toolkit.runtime.use_runtime`, or by whatever process wires up
`gha_toolkit.runtime.create_runtime`'s result under real GitHub Actions usage)
and delegates to exactly one of that runtime's nine composed services'
methods -- named in each function's own docstring. There is no class here for
a user to instantiate: `from gha_toolkit import core; core.info('hello')` /
`core.get_context()` / `core.get_inputs(MyInputs)` is the complete surface
this module offers, mirroring how upstream `@actions/core` is consumed as a
flat module of functions, not a class.

Parity surface: every function upstream `core.ts` exports at module scope
(`getInput`, `getBooleanInput`, `getMultilineInput`, `setOutput`,
`exportVariable`, `addPath`, `saveState`, `getState`, `setSecret`,
`setCommandEcho`, `setFailed`, `isDebug`, `debug`/`info`/`notice`/`warning`/
`error`, `startGroup`/`endGroup`/`group`) plus this package's own additions
(`get_context`, `get_inputs`, an async `get_id_token`, and a step-summary
accessor). `group` is a context manager, not upstream's async wrapper
function -- see `gha_toolkit.logger.ActionsLogger.group` for why.

This is an interface-only module: every function below raises
``NotImplementedError``.
"""

import contextlib
from collections.abc import Sequence
from typing import TypeVar

from gha_toolkit.commands import AnnotationOptions, ExitCode, OutputValue
from gha_toolkit.context import GitHubContext
from gha_toolkit.summary import ActionStepSummary

ModelT = TypeVar('ModelT')
ModelT.__doc__ = """Type parameter for :func:`get_inputs`'s bound dataclass and return value.

Fixed by whatever dataclass type the caller passes as `model_type`; mirrors
`gha_toolkit.binder.get_inputs`'s own type parameter.
"""


def get_input(name: str, *, required: bool = False, trim: bool = True) -> str:
    """Return workflow input `name` as a plain string.

    Resolves the current runtime and delegates to
    `ActionsRuntime.inputs.get_string`.

    Raises:
        gha_toolkit.exceptions.MissingInputError: see
            `gha_toolkit.inputs.ActionsInputs.get`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_boolean_input(name: str, *, required: bool = False, trim: bool = True) -> bool:
    """Return workflow input `name` parsed as a YAML 1.2 core-schema boolean.

    Resolves the current runtime and delegates to
    `ActionsRuntime.inputs.get_boolean`.

    Raises:
        gha_toolkit.exceptions.MissingInputError: see
            `gha_toolkit.inputs.ActionsInputs.get`.
        gha_toolkit.exceptions.InputParseError: see
            `gha_toolkit.inputs.ActionsInputs.get_boolean`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_multiline_input(
    name: str, *, required: bool = False, trim: bool = True
) -> Sequence[str]:
    """Return workflow input `name` split into a list of non-empty lines.

    Resolves the current runtime and delegates to
    `ActionsRuntime.inputs.get_multiline`.

    Raises:
        gha_toolkit.exceptions.MissingInputError: see
            `gha_toolkit.inputs.ActionsInputs.get`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_context() -> GitHubContext:
    """Return the triggering workflow run's typed context.

    Resolves the current runtime via `gha_toolkit.runtime.current_runtime`
    -- so calling this with no runtime bound fails the same way every other
    facade function does -- then delegates to `gha_toolkit.binder.get_context`
    reading live process environment variables directly: `GithubEnvironment`
    (`ActionsRuntime.environment`) does not expose the mapping it wraps, so
    this does not route through it, unlike every other function in this
    module.

    Raises:
        gha_toolkit.exceptions.EventPayloadError: see
            `gha_toolkit.binder.get_context`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_inputs(model_type: type[ModelT]) -> ModelT:
    """Build `model_type` from this step's `with:` inputs.

    Resolves the current runtime via `gha_toolkit.runtime.current_runtime`
    for the same reason `get_context` does, then delegates to
    `gha_toolkit.binder.get_inputs` reading live process environment
    variables directly (see `get_context`'s docstring for why this bypasses
    `ActionsRuntime.environment`).

    Raises:
        gha_toolkit.exceptions.MissingInputError: see
            `gha_toolkit.binder.get_inputs`.
        gha_toolkit.exceptions.InputParseError: see
            `gha_toolkit.binder.get_inputs`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def set_output(name: str, value: OutputValue) -> None:
    """Set this step's output `name` to `value`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.output.set`.

    Raises:
        gha_toolkit.exceptions.DelimiterInjectionError: see
            `gha_toolkit.services.ActionsOutput.set`.
        gha_toolkit.exceptions.MissingRunnerFileError: see
            `gha_toolkit.services.ActionsOutput.set`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def export_variable(name: str, value: OutputValue) -> None:
    """Set `name` to `value` in this step's live environment and every later step's.

    Resolves the current runtime and delegates to two of its services:
    `ActionsRuntime.environment.set` (the live process environment, visible
    immediately to code running later in this same process) and
    `ActionsRuntime.files.env.set` (a delimiter-framed heredoc block
    appended to `GITHUB_ENV`, visible to every later step in the job).
    Parity with upstream `exportVariable`, minus its `PATH`-specific
    prepend branch -- see `add_path` for that.

    Raises:
        gha_toolkit.exceptions.DelimiterInjectionError: see
            `gha_toolkit.files.KeyValueFile.set`.
        gha_toolkit.exceptions.MissingRunnerFileError: see
            `gha_toolkit.files.KeyValueFile.set`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def add_path(path: str) -> None:
    """Prepend `path` to `PATH`, for the runner-wide list and this process.

    Resolves the current runtime and delegates to
    `ActionsRuntime.paths.add`.

    Raises:
        gha_toolkit.exceptions.MissingRunnerFileError: see
            `gha_toolkit.services.ActionsPaths.add`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def save_state(name: str, value: OutputValue) -> None:
    """Save state entry `name` as `value` for this action's post-job execution.

    Resolves the current runtime and delegates to
    `ActionsRuntime.state.save`.

    Raises:
        gha_toolkit.exceptions.DelimiterInjectionError: see
            `gha_toolkit.services.ActionsState.save`.
        gha_toolkit.exceptions.MissingRunnerFileError: see
            `gha_toolkit.services.ActionsState.save`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def get_state(name: str) -> str:
    """Return the value this action previously saved for state entry `name`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.state.get`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def set_secret(secret: str) -> None:
    """Instruct the runner to mask `secret` in all subsequent log output.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.set_secret`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def set_command_echo(*, enabled: bool) -> None:
    """Turn workflow-command echoing to the log on or off.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.set_command_echo`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def set_failed(message: str | Exception) -> ExitCode:
    """Mark this step as failed and emit an error annotation for `message`.

    Resolves the current runtime and delegates to `ActionsRuntime.logger.error`
    with `message` (or `str(message)` when an `Exception` is given, parity
    with upstream `setFailed`), then returns `ExitCode.FAILURE`. Parity
    deviation: upstream sets `process.exitCode` as a side effect and returns
    nothing; Python has no equivalent deferred process-exit-code global, so
    this returns the exit code for the caller to act on instead -- for
    example `raise SystemExit(core.set_failed(exc))`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def is_debug() -> bool:
    """Return whether `RUNNER_DEBUG` is set to exactly `'1'`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.is_debug`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def debug(message: str) -> None:
    """Issue a `'::debug::'` command carrying `message`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.debug`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def info(message: str) -> None:
    """Write `message` straight to the log, with no `::` command framing.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.info`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def notice(message: str, options: AnnotationOptions | None = None) -> None:
    """Issue a `'::notice ...::'` annotation command carrying `message`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.notice`, passing `options` through unchanged.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def warning(message: str, options: AnnotationOptions | None = None) -> None:
    """Issue a `'::warning ...::'` annotation command carrying `message`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.warning`, passing `options` through unchanged.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def error(message: str, options: AnnotationOptions | None = None) -> None:
    """Issue a `'::error ...::'` annotation command carrying `message`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.error`, passing `options` through unchanged.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def start_group(name: str) -> None:
    """Issue a `'::group::{name}'` command, opening a foldable log group.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.start_group`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def end_group() -> None:
    """Issue a `'::endgroup::'` command, closing the current log group.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.end_group`.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def group(name: str) -> contextlib.AbstractContextManager[None]:
    """Return a context manager wrapping a block in a start/end group pair.

    Resolves the current runtime and delegates to
    `ActionsRuntime.logger.group`: `with core.group(name): ...` calls
    `start_group` on entry and guarantees `end_group` runs on exit,
    including when the wrapped block raises.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


async def get_id_token(audience: str | None = None) -> str:
    """Request and return an OIDC ID token, optionally scoped to `audience`.

    Resolves the current runtime and delegates to
    `ActionsRuntime.oidc.get_id_token`.

    Raises:
        gha_toolkit.exceptions.OidcFailureError: see
            `gha_toolkit.oidc.OidcClient.get_id_token`.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def summary() -> ActionStepSummary:
    """Return this step's job-summary accessor.

    Resolves the current runtime and delegates to
    `ActionsRuntime.step_summary`: `core.summary().buffer.add_heading(...)`
    then `core.summary().write()` is how a caller builds and flushes the job
    summary through this facade.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError
