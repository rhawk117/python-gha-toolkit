"""The command-sink seam: where a rendered workflow command actually goes.

:func:`gha_toolkit.commands.format_command` renders an :class:`ActionCommand
<gha_toolkit.commands.ActionCommand>` into its final wire string but has no opinion
about where that string is delivered. :class:`CommandSink` is that opinion,
factored out as a protocol so the same rendering pipeline can target stdout (this
module's :class:`StdoutSink`) or a runner file (``gha_toolkit.files``) without
either transport knowing about the other.

This is an interface-only module: :class:`StdoutSink`'s behavior method raises
``NotImplementedError``. :class:`CommandSink` and :class:`SinkStream` are
protocols -- there is no behavior to implement, only shape to satisfy -- and
:class:`FlushPolicy` is a pure enum; both stand as real definitions.
"""

import enum
import sys
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from gha_toolkit.commands import ActionCommand, OutputValue


@runtime_checkable
class CommandSink(Protocol):
    """The seam every command transport implements: something that can `invoke`.

    A minimal protocol by design -- its sole public member is :meth:`invoke` -- so
    that any object with a matching `invoke(command) -> None` method satisfies it
    structurally, without needing to inherit from this class. Decorated
    `@runtime_checkable` so callers may `isinstance()`-check a candidate sink.
    """

    def invoke(self, command: ActionCommand[Mapping[str, OutputValue]]) -> None:
        """Deliver `command` to this sink's transport.

        What "deliver" means is entirely up to the implementation: writing a
        rendered string to a stream, appending to a runner file, and so on.
        """
        ...


@runtime_checkable
class SinkStream(Protocol):
    """Structural contract for anything :class:`StdoutSink` can write to.

    Deliberately small -- `write(str) -> object` and `flush() -> object` -- so
    that both real streams (`sys.stdout`) and test doubles (for example
    `tests/fixtures/sink_recorder.WriteRecorder`) satisfy it without inheriting
    from this class. Return types are `object` rather than `int` / `None` because
    implementations disagree (`TextIOWrapper.write` returns `int`; a recorder's
    `write` returns `None`) and this seam does not use the return value.
    """

    def write(self, data: str, /) -> object:
        """Write `data` to the underlying stream."""
        ...

    def flush(self) -> object:
        """Flush any data buffered by the underlying stream."""
        ...


class FlushPolicy(enum.Enum):
    """When :class:`StdoutSink` flushes its bound stream after a write.

    Python block-buffers stdout whenever it is not attached to a TTY -- which is
    exactly the case for a GitHub Actions runner, where step output is captured
    through a pipe -- so a write is not guaranteed to reach the log promptly
    unless something flushes explicitly. This is the reason `StdoutSink` exists
    as a small stream-writing seam instead of calling `print()` directly: `print()`
    offers no flush-policy control, and workflow commands must appear in the log
    for the runner to parse them.

    Members:
      PER_COMMAND: flush the stream after every :meth:`StdoutSink.invoke` call.
      NEVER: never flush explicitly; rely on the stream's own buffering policy
        (or process exit) to deliver writes.
    """

    PER_COMMAND = enum.auto()
    NEVER = enum.auto()


class StdoutSink:
    """A :class:`CommandSink` that writes rendered commands to a stream.

    Renders each command via :func:`gha_toolkit.commands.format_command` and
    writes the rendered string plus `os.linesep` to the bound stream, then
    applies the bound :class:`FlushPolicy`. Constructing an instance never
    itself performs I/O; only :meth:`invoke` does.
    """

    def __init__(
        self,
        stream: SinkStream | None = None,
        *,
        flush_policy: FlushPolicy = FlushPolicy.PER_COMMAND,
    ) -> None:
        """Bind this sink to `stream` (default: `sys.stdout`) under `flush_policy`.

        Storing the stream and policy is the entire constructor; no I/O happens
        here.
        """
        self._stream: SinkStream = stream if stream is not None else sys.stdout
        self._flush_policy = flush_policy

    def invoke(self, command: ActionCommand[Mapping[str, OutputValue]]) -> None:
        """Render `command` and write it plus `os.linesep` to the bound stream.

        Renders via :func:`gha_toolkit.commands.format_command`, writes the
        result followed by `os.linesep` to the bound stream, then flushes the
        stream if and only if the bound :class:`FlushPolicy` is `PER_COMMAND`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
