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

import dataclasses
import enum
import sys
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from gha_toolkit.commands import ActionCommand, OutputValue


@runtime_checkable
class CommandSink(Protocol):
    def invoke(self, command: ActionCommand[Mapping[str, OutputValue]]) -> None: ...


@runtime_checkable
class SinkStream(Protocol):
    def write(self, data: str, /) -> object: ...

    def flush(self) -> object: ...


class FlushPolicy(enum.Enum):
    PER_COMMAND = enum.auto()
    NEVER = enum.auto()


@dataclasses.dataclass(slots=True)
class StdoutSink:
    stream: SinkStream = dataclasses.field(default_factory=lambda: sys.stdout)
    flush_policy: FlushPolicy = dataclasses.field(
        default=FlushPolicy.PER_COMMAND, kw_only=True
    )

    def invoke(self, command: ActionCommand[Mapping[str, OutputValue]]) -> None:
        raise NotImplementedError
