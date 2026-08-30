"""Wire primitives for the GitHub Actions workflow-command protocol.

This module defines the low-level contract every command sink (stdout, file-based
sinks) is built on: how arbitrary Python values are serialized to the wire
(:func:`to_command_value`), how that serialization is escaped for the ``::name
key=value::message`` command format (:func:`escape_data`, :func:`escape_property`),
how a fully-populated command renders to its final string
(:func:`format_command`), and the typed payloads that flow through that pipeline
(:class:`ActionCommand`, :class:`AnnotationOptions`, :class:`ExitCode`).

This is an interface-only module: every function below raises ``NotImplementedError``.
Only pure data definitions (the dataclass field lists, the enum) are real.
`AnnotationOptions`'s validation logic lives in the module-level
:func:`make_annotation_options` factory function, not in the dataclass's
constructor. Invariants it enforces (decisions of record -- issue #4
decision 5 -- the upstream TypeScript interface documented these as caller
responsibility but never enforced them):

- `end_line` defaults to `start_line` when a start line is given but no end
  line is.
- `end_column` defaults to `start_column` when a start column is given but
  no end column is.
- `start_column`/`end_column` must not be set when `start_line` and
  `end_line` differ -- a column position is only meaningful within a
  single-line span.

Violating an invariant raises :class:`gha_toolkit.exceptions.InvalidAnnotationError`.

Ported from ``.original/toolkit/packages/core/src/{utils,command,core}.ts``; parity
is byte-level on rendered command strings.
"""

import dataclasses
import enum
from collections.abc import Mapping, Sequence
from typing import Generic, TypeVar

OutputValue = (
    str
    | bool
    | int
    | float
    | None
    | Mapping[str, 'OutputValue']
    | Sequence['OutputValue']
)

OptionsT = TypeVar('OptionsT', bound=Mapping[str, OutputValue])


def to_command_value(value: OutputValue) -> str:
    raise NotImplementedError


def escape_data(value: OutputValue) -> str:
    raise NotImplementedError


def escape_property(value: OutputValue) -> str:
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class ActionCommand(Generic[OptionsT]):
    name: str
    properties: OptionsT
    message: OutputValue


def format_command(command: ActionCommand[OptionsT]) -> str:
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class AnnotationOptions:
    title: str | None = None
    file: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None


def make_annotation_options(
    *,
    title: str | None = None,
    file: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    start_column: int | None = None,
    end_column: int | None = None,
) -> AnnotationOptions:
    raise NotImplementedError


class ExitCode(enum.IntEnum):
    SUCCESS = 0
    FAILURE = 1
