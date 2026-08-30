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
that composes this package's services, not to the logger itself.

This is an interface-only module: every behavior method on
:class:`WorkflowLogger`, the minimal concrete stub for the
:class:`ActionsLogger` protocol, raises ``NotImplementedError``.
"""

import contextlib
import dataclasses
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from gha_toolkit.commands import AnnotationOptions, OutputValue
from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.sinks import CommandSink, SinkStream


def _annotation_properties(
    options: AnnotationOptions | None,
) -> Mapping[str, OutputValue]:
    raise NotImplementedError


@runtime_checkable
class ActionsLogger(Protocol):
    def debug(self, message: str) -> None: ...

    def info(self, message: str) -> None: ...

    def notice(
        self, message: str, options: AnnotationOptions | None = None
    ) -> None: ...

    def warning(
        self, message: str, options: AnnotationOptions | None = None
    ) -> None: ...

    def error(self, message: str, options: AnnotationOptions | None = None) -> None: ...

    def is_debug(self) -> bool: ...

    def set_secret(self, secret: str) -> None: ...

    def set_command_echo(self, *, enabled: bool) -> None: ...

    def start_group(self, name: str) -> None: ...

    def end_group(self) -> None: ...

    def group(self, name: str) -> contextlib.AbstractContextManager[None]: ...


@dataclasses.dataclass(slots=True)
class WorkflowLogger:
    sink: CommandSink
    stream: SinkStream
    environment: GithubEnvironment

    def debug(self, message: str) -> None:
        raise NotImplementedError

    def info(self, message: str) -> None:
        raise NotImplementedError

    def notice(self, message: str, options: AnnotationOptions | None = None) -> None:
        raise NotImplementedError

    def warning(self, message: str, options: AnnotationOptions | None = None) -> None:
        raise NotImplementedError

    def error(self, message: str, options: AnnotationOptions | None = None) -> None:
        raise NotImplementedError

    def is_debug(self) -> bool:
        raise NotImplementedError

    def set_secret(self, secret: str) -> None:
        raise NotImplementedError

    def set_command_echo(self, *, enabled: bool) -> None:
        raise NotImplementedError

    def start_group(self, name: str) -> None:
        raise NotImplementedError

    def end_group(self) -> None:
        raise NotImplementedError

    def group(self, name: str) -> contextlib.AbstractContextManager[None]:
        raise NotImplementedError
