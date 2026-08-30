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
"""The set of Python values accepted anywhere a command value is expected.

Python counterpart of the ``any`` accepted by upstream ``toCommandValue`` /
``issueCommand``, narrowed to the shapes :func:`to_command_value` actually knows
how to serialize: ``str``, ``bool``, ``int``, ``float``, ``None``, and JSON-shaped
``Mapping``/``Sequence`` containers of the same.
"""

OptionsT = TypeVar('OptionsT', bound=Mapping[str, OutputValue])
OptionsT.__doc__ = """Type parameter for :class:`ActionCommand`'s properties/options payload.

Bound to ``Mapping[str, OutputValue]`` because :func:`format_command` renders the
payload as comma-joined ``key=value`` pairs; every concrete command site (plain
workflow commands, annotation commands, etc.) supplies its own mapping shape as
this parameter.
"""


def to_command_value(value: OutputValue) -> str:
    """Serialize an arbitrary value into the string form the runner expects.

    Serialization policy (parity with ``utils.ts:11-18`` ``toCommandValue``):
      - ``None`` -> ``''``
      - ``str`` -> returned unchanged
      - everything else -> its JSON serialization, byte-identical to JavaScript's
        ``JSON.stringify`` (compact separators, lowercase ``true``/``false``/
        ``null``)

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def escape_data(value: OutputValue) -> str:
    """Escape a value for use as a workflow command's message segment.

    Runs :func:`to_command_value` on ``value`` first, then applies the following
    substitutions in order (parity with ``command.ts:103-108`` ``escapeData``):
      1. ``%`` -> ``%25``
      2. ``\\r`` -> ``%0D``
      3. ``\\n`` -> ``%0A``

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def escape_property(value: OutputValue) -> str:
    """Escape a value for use as a workflow command's property value.

    Runs :func:`to_command_value` on ``value`` first, then applies the same three
    substitutions as :func:`escape_data`, followed by two more, all in order
    (parity with ``command.ts:110-117`` ``escapeProperty``):
      1. ``%`` -> ``%25``
      2. ``\\r`` -> ``%0D``
      3. ``\\n`` -> ``%0A``
      4. ``:`` -> ``%3A``
      5. ``,`` -> ``%2C``

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class ActionCommand(Generic[OptionsT]):
    """An immutable workflow-command payload, ready for rendering by format_command.

    Parity counterpart of the internal ``Command`` class (``core.ts``/``command.ts``,
    command.ts:61-101): a command name, a properties/options payload generic over
    ``OptionsT`` (bound to ``Mapping[str, OutputValue]``), and a message. Frozen and
    slotted: instances are value objects and are never mutated after construction;
    assigning to an attribute raises ``dataclasses.FrozenInstanceError``.

    :func:`format_command` is the only primitive that interprets these fields;
    sinks (stdout, file-based command sinks) call it and write the result.
    """

    name: str
    properties: OptionsT
    message: OutputValue


def format_command(command: ActionCommand[OptionsT]) -> str:
    """Render an ActionCommand into its final ``::name ...::message`` wire string.

    Rendering (parity with ``command.ts:59-101`` ``Command.toString``):
      - Starts with the literal ``'::'`` followed by ``command.name``; an empty
        (falsy) name renders as ``'missing.command'`` instead.
      - If ``command.properties`` is non-empty, a single space is appended, then
        comma-joined ``key=escape_property(value)`` pairs in iteration order.
        Properties whose value is falsy in the JavaScript sense (``None``, ``''``,
        ``0``, ``False``) are SKIPPED entirely rather than rendered as ``key=`` —
        this is a parity detail carried over from upstream's ``if (val)`` guard.
      - Then the literal ``'::'`` again, followed by ``escape_data(command.message)``.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class AnnotationOptions:
    """Optional properties for annotation commands (notice, warning, error).

    Snake_case counterpart of upstream ``AnnotationProperties``
    (``core.ts:40-71``). All six fields default to ``None``; an annotation may
    specify none, some, or all of them.

    Invariants enforced by this project (decisions of record — the upstream
    TypeScript interface documented these as caller responsibility but never
    enforced them):
      - ``end_line`` defaults to ``start_line`` when a start line is given but no
        end line is.
      - ``end_column`` defaults to ``start_column`` when a start column is given
        but no end column is.
      - ``start_column``/``end_column`` must not be set when ``start_line`` and
        ``end_line`` differ — a column position is only meaningful within a
        single-line span.

    Violating an invariant raises ``gha_toolkit.exceptions.InvalidAnnotationError``
    once validation is implemented. For now, construction unconditionally invokes
    a validation stub that raises ``NotImplementedError``.
    """

    title: str | None = None
    file: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Validate the line/column invariants documented on this class.

        Raises:
            NotImplementedError: always; validation logic (culminating in
                ``gha_toolkit.exceptions.InvalidAnnotationError`` on a violation)
                lands in a later task.
        """
        raise NotImplementedError


class ExitCode(enum.IntEnum):
    """Process exit codes the Actions runner recognizes as an action's outcome.

    Parity with upstream ``ExitCode`` (``core.ts``, ~lines 24-34): the process
    exiting with ``SUCCESS`` marks the step as passing; exiting with ``FAILURE``
    marks it failed.
    """

    SUCCESS = 0
    FAILURE = 1
