"""The job step summary pair: a fluent HTML/markdown buffer and its file binding.

Upstream `summary.ts` folds two responsibilities into one `Summary` class: a
pure in-memory string buffer (`addRaw`, `addHeading`, `addTable`, ...) and the
I/O that flushes that buffer to the `GITHUB_STEP_SUMMARY` file (`write`,
`clear`). This module keeps the buffer -- :class:`ActionSummary` -- and the
I/O separate.

:class:`SummaryBuffer` is the narrow lifecycle trio -- `stringify`,
`is_empty`, `clear` -- that :meth:`StepSummaryWriter.write` and
:meth:`StepSummaryWriter.clear`'s own bodies actually call on their bound
buffer; :class:`ActionSummary` extends it with the fluent element-builder
methods (`add_raw`, `add_heading`, `add_table`, ...) that a caller holding a
`StepSummaryWriter` also needs through the same `buffer` attribute to build
content in the first place (`step_summary.buffer.add_raw(...)`, the pattern
every call site in this package uses). `StepSummaryWriter.buffer` is
therefore typed against the wider `ActionSummary`, not the narrow
`SummaryBuffer`, even though the writer's own internal contract only draws
on the narrow trio -- narrowing the field itself would take builder access
away from every external caller through the one attribute they have.

:class:`ActionSummary` is a protocol for a pure, reusable, in-memory string
builder with no knowledge of any runner file; its minimal concrete stub,
:class:`HtmlSummaryBuffer`, can be constructed and used anywhere, including
outside a GitHub Actions runner (in tests, in scripts that only want the HTML
rendering). :class:`ActionStepSummary` is the protocol for the file-bound
half: it binds an `ActionSummary`-shaped buffer together with a
:class:`gha_toolkit.files.StepSummaryFile` and owns `write()` / `clear()` --
the operations that actually touch the `GITHUB_STEP_SUMMARY` file; its
minimal concrete stub is :class:`StepSummaryWriter`, whose `buffer` is a
required constructor argument -- `gha_toolkit.runtime.create_runtime` is the
composition root that supplies `HtmlSummaryBuffer` as the default buffer
implementation, not a default on this dataclass.

This split is a design decision of record, not an upstream detail: nothing in
`summary.ts` separates the buffer from the file. It exists so
`ActionSummary` stays a plain value-like shape callers can build, inspect
(`stringify()`), and discard without ever touching a runner file.

Ported from ``.original/toolkit/packages/core/src/summary.ts``. Every element
builder on `ActionSummary` follows the same two-step shape upstream's private
`wrap()` helper produces: wrap the caller's content in an HTML tag, with the
tag's attributes rendered as `' key="value"'` pairs in insertion order (a
"void" element such as `<hr>` or `<img ...>`, whose content is `None` or
empty, renders as `<tag attrs>` with no closing tag); then append the
rendered element to the buffer, followed by `os.linesep`.

This is an interface-only module: every behavior method on
:class:`HtmlSummaryBuffer` and :class:`StepSummaryWriter` raises
``NotImplementedError``. :class:`SummaryTableCell` and
:class:`SummaryImageOptions` are pure data definitions and are real.
"""

import dataclasses
from collections.abc import Sequence
from typing import Protocol, Self, runtime_checkable

from gha_toolkit.files import StepSummaryFile


@dataclasses.dataclass(frozen=True, slots=True)
class SummaryTableCell:
    data: str
    header: bool = False
    colspan: str | None = None
    rowspan: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class SummaryImageOptions:
    width: str | None = None
    height: str | None = None


SummaryTableRow = Sequence[SummaryTableCell | str]


@runtime_checkable
class SummaryBuffer(Protocol):
    def stringify(self) -> str: ...

    def is_empty(self) -> bool: ...

    def clear(self) -> Self: ...


@runtime_checkable
class ActionSummary(SummaryBuffer, Protocol):
    def add_raw(self, text: str, *, add_eol: bool = False) -> Self: ...

    def add_eol(self) -> Self: ...

    def add_code_block(self, code: str, lang: str | None = None) -> Self: ...

    def add_list(self, items: Sequence[str], *, ordered: bool = False) -> Self: ...

    def add_table(self, rows: Sequence[SummaryTableRow]) -> Self: ...

    def add_details(self, label: str, content: str) -> Self: ...

    def add_image(
        self, src: str, alt: str, options: SummaryImageOptions | None = None
    ) -> Self: ...

    def add_heading(self, text: str, level: int | str = 1) -> Self: ...

    def add_separator(self) -> Self: ...

    def add_break(self) -> Self: ...

    def add_quote(self, text: str, cite: str | None = None) -> Self: ...

    def add_link(self, text: str, href: str) -> Self: ...


@dataclasses.dataclass(slots=True)
class HtmlSummaryBuffer:
    content: str = ''

    def _wrap(
        self,
        tag: str,
        content: str | None,
        attrs: dict[str, str] | None = None,
    ) -> str:
        raise NotImplementedError

    def add_raw(self, text: str, *, add_eol: bool = False) -> Self:
        raise NotImplementedError

    def add_eol(self) -> Self:
        raise NotImplementedError

    def add_code_block(self, code: str, lang: str | None = None) -> Self:
        raise NotImplementedError

    def add_list(self, items: Sequence[str], *, ordered: bool = False) -> Self:
        raise NotImplementedError

    def add_table(self, rows: Sequence[SummaryTableRow]) -> Self:
        raise NotImplementedError

    def add_details(self, label: str, content: str) -> Self:
        raise NotImplementedError

    def add_image(
        self,
        src: str,
        alt: str,
        options: SummaryImageOptions | None = None,
    ) -> Self:
        raise NotImplementedError

    def add_heading(self, text: str, level: int | str = 1) -> Self:
        raise NotImplementedError

    def add_separator(self) -> Self:
        raise NotImplementedError

    def add_break(self) -> Self:
        raise NotImplementedError

    def add_quote(self, text: str, cite: str | None = None) -> Self:
        raise NotImplementedError

    def add_link(self, text: str, href: str) -> Self:
        raise NotImplementedError

    def stringify(self) -> str:
        raise NotImplementedError

    def is_empty(self) -> bool:
        raise NotImplementedError

    def clear(self) -> Self:
        raise NotImplementedError


@runtime_checkable
class ActionStepSummary(Protocol):
    buffer: ActionSummary

    def write(self, *, overwrite: bool = False) -> Self: ...

    def clear(self) -> Self: ...


@dataclasses.dataclass(slots=True)
class StepSummaryWriter:
    step_summary_file: StepSummaryFile
    buffer: ActionSummary

    def write(self, *, overwrite: bool = False) -> Self:
        raise NotImplementedError

    def clear(self) -> Self:
        raise NotImplementedError
