"""The step-log seam: workflow log commands, annotations, and output groups.

Every operation here renders to one of two transports: most methods issue a
fully-framed `::name ...::message` workflow command through a bound
:class:`gha_toolkit.sinks.CommandSink`; :meth:`ActionsLogger.info` is the one
exception, writing its message straight to a bound
:class:`gha_toolkit.sinks.SinkStream` with no `::` framing at all -- parity
with upstream `info` calling `process.stdout.write` directly rather than going
through `issueCommand`. `is_debug` reads `RUNNER_DEBUG` from a bound
:class:`gha_toolkit.environment.GithubEnvironment`, since that variable is
plain process environment, not a workflow command.

Ported from ``.original/toolkit/packages/core/src/core.ts`` (`core.ts:124-131`
`setSecret`, `232-243` `setCommandEcho`, `258-260` `isDebug`, `266-350`
`debug`/`error`/`warning`/`notice`/`info`/`startGroup`/`endGroup`/`group`) and
``.original/toolkit/packages/core/src/utils.ts:26-41`` (`toCommandProperties`,
the annotation-options-to-command-properties mapping). Deviation of record:
upstream's `group` is an async wrapper around a caller-supplied async
function; this package's core is synchronous, so :meth:`ActionsLogger.group`
is a context manager instead (`with logger.group(name): ...`), guaranteeing
`end_group` runs in a `finally` the same way upstream's `try`/`finally`
around the wrapped call does. `set_failed` and :class:`gha_toolkit.commands.ExitCode`
are deliberately absent from this class -- they belong to the runtime facade
that composes this package's services, a later task, not to the logger itself.

This is an interface-only module: every behavior method below raises
``NotImplementedError``. Only the constructor, which stores its arguments, is
real.
"""

import contextlib
from collections.abc import Mapping

from gha_toolkit.commands import AnnotationOptions, OutputValue
from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.sinks import CommandSink, SinkStream


def _annotation_properties(
    options: AnnotationOptions | None,
) -> Mapping[str, OutputValue]:
    """Map `options` onto the command-property keys `notice`/`warning`/`error` render.

    Parity with upstream `toCommandProperties` (`utils.ts:26-41`): `None`
    (no options supplied) maps to an empty mapping, so the rendered command
    carries no properties segment at all. A supplied :class:`AnnotationOptions`
    maps its snake_case fields onto the six command property keys upstream
    uses, under a renamed key on three of them:
      - `title` -> `'title'`
      - `file` -> `'file'`
      - `start_line` -> `'line'`
      - `end_line` -> `'endLine'`
      - `start_column` -> `'col'`
      - `end_column` -> `'endColumn'`
    All six keys are always present in the returned mapping when `options` is
    not `None`, `None`-valued fields included; it is
    :func:`gha_toolkit.commands.format_command` that skips falsy-valued
    properties when rendering, not this function.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


class ActionsLogger:
    """Workflow log commands, annotations, secret masking, and output groups.

    Two bound transports, corresponding to the two ways upstream `@actions/core`
    writes to the log: a :class:`gha_toolkit.sinks.CommandSink` for every
    `::name ...::message`-framed command (`debug`, `notice`/`warning`/`error`,
    `set_secret`, `set_command_echo`, `start_group`/`end_group`), and a
    :class:`gha_toolkit.sinks.SinkStream` for :meth:`info`'s unframed
    passthrough write. A bound :class:`gha_toolkit.environment.GithubEnvironment`
    backs :meth:`is_debug`, which reads a plain environment variable rather
    than issuing or reading a command.
    """

    def __init__(
        self,
        sink: CommandSink,
        stream: SinkStream,
        environment: GithubEnvironment,
    ) -> None:
        """Bind this instance to `sink`, `stream`, and `environment`.

        Storing the three references is the entire constructor; no command is
        issued and no environment variable is read until a method below is
        called.
        """
        self._sink = sink
        self._stream = stream
        self._environment = environment

    def debug(self, message: str) -> None:
        """Issue a `'::debug::'` command carrying `message`.

        Parity with upstream `debug` (`core.ts:266-268`): equivalent to
        `issueCommand('debug', {}, message)` -- no properties, routed through
        the bound sink.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def info(self, message: str) -> None:
        """Write `message` plus a line separator straight to the bound stream.

        Parity with upstream `info` (`core.ts:322-324`,
        `process.stdout.write(message + os.EOL)`): no `::` command framing,
        and not routed through the bound :class:`gha_toolkit.sinks.CommandSink`
        at all -- this is the one method on this class that writes to
        `stream` instead of `sink`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def notice(self, message: str, options: AnnotationOptions | None = None) -> None:
        """Issue a `'::notice ...::'` annotation command carrying `message`.

        Parity with upstream `notice` (`core.ts:307-319`): properties are
        `options` mapped through :func:`_annotation_properties`, routed
        through the bound sink alongside `message`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def warning(self, message: str, options: AnnotationOptions | None = None) -> None:
        """Issue a `'::warning ...::'` annotation command carrying `message`.

        Parity with upstream `warning` (`core.ts:291-303`): properties are
        `options` mapped through :func:`_annotation_properties`, routed
        through the bound sink alongside `message`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def error(self, message: str, options: AnnotationOptions | None = None) -> None:
        """Issue a `'::error ...::'` annotation command carrying `message`.

        Parity with upstream `error` (`core.ts:275-287`): properties are
        `options` mapped through :func:`_annotation_properties`, routed
        through the bound sink alongside `message`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def is_debug(self) -> bool:
        """Return whether `RUNNER_DEBUG` is set to exactly `'1'`.

        Parity with upstream `isDebug` (`core.ts:258-260`,
        `process.env['RUNNER_DEBUG'] === '1'`): reads `RUNNER_DEBUG` from the
        bound environment; any value other than the literal string `'1'`
        (including unset) is `False`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def set_secret(self, secret: str) -> None:
        """Issue a `'::add-mask::'` command carrying `secret`.

        Parity with upstream `setSecret` (`core.ts:124-131`,
        `issueCommand('add-mask', {}, secret)`): instructs the runner to mask
        `secret` in all subsequent log output.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def set_command_echo(self, *, enabled: bool) -> None:
        """Issue a `'::echo::on'` or `'::echo::off'` command.

        Parity with upstream `setCommandEcho` (`core.ts:232-234`,
        `issue('echo', enabled ? 'on' : 'off')`): `True` renders `'on'`,
        `False` renders `'off'`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def start_group(self, name: str) -> None:
        """Issue a `'::group::{name}'` command, opening a foldable log group.

        Parity with upstream `startGroup` (`core.ts:333-335`,
        `issue('group', name)`). Output written after this call is foldable
        under `name` in the runner's log UI until :meth:`end_group` is called.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def end_group(self) -> None:
        """Issue a `'::endgroup::'` command, closing the current log group.

        Parity with upstream `endGroup` (`core.ts:340-342`, `issue('endgroup')`).

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def group(self, name: str) -> contextlib.AbstractContextManager[None]:
        """Return a context manager wrapping a block in a `start_group`/`end_group` pair.

        Parity with upstream `group` (`core.ts:352-365`), adapted from an
        async function wrapper to a context manager since this package's core
        is synchronous: `with logger.group(name): ...` calls
        :meth:`start_group` on entry and guarantees :meth:`end_group` runs on
        exit -- including when the wrapped block raises -- the same way
        upstream's `try`/`finally` around the wrapped async call does.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
