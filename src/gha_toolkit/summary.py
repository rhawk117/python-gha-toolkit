"""The job step summary pair: a fluent HTML/markdown buffer and its file binding.

Upstream `summary.ts` folds two responsibilities into one `Summary` class: a
pure in-memory string buffer (`addRaw`, `addHeading`, `addTable`, ...) and the
I/O that flushes that buffer to the `GITHUB_STEP_SUMMARY` file (`write`,
`clear`). This module keeps the buffer -- :class:`ActionSummary` -- and the
I/O separate.

:class:`ActionSummary` is a pure, reusable, in-memory string builder with no
knowledge of any runner file; it can be constructed and used anywhere,
including outside a GitHub Actions runner (in tests, in scripts that only want
the HTML rendering). :class:`ActionStepSummary` is the file-bound half: it
wraps an :class:`ActionSummary` buffer together with a
:class:`gha_toolkit.files.StepSummaryFile` and owns `write()` / `clear()` --
the operations that actually touch the `GITHUB_STEP_SUMMARY` file.

This split is a design decision of record, not an upstream detail: nothing in
`summary.ts` separates the buffer from the file. It exists so
`ActionSummary` stays a plain value-like object callers can build, inspect
(`stringify()`), and discard without ever touching a runner file.

Ported from ``.original/toolkit/packages/core/src/summary.ts``. Every element
builder on `ActionSummary` follows the same two-step shape upstream's private
`wrap()` helper produces: wrap the caller's content in an HTML tag, with the
tag's attributes rendered as `' key="value"'` pairs in insertion order (a
"void" element such as `<hr>` or `<img ...>`, whose content is `None` or
empty, renders as `<tag attrs>` with no closing tag); then append the
rendered element to the buffer, followed by `os.linesep`. This module cites
that shared shape once here rather than repeating it in each builder's
docstring; each builder documents only its tag, its attributes, and their
order.

This is an interface-only module: every behavior method below raises
``NotImplementedError``. :class:`SummaryTableCell` and
:class:`SummaryImageOptions` are pure data definitions and are real. Only
constructors (which store their arguments and, for `ActionSummary`,
initialize an empty buffer; no I/O happens at construction time for either
class) are real.
"""

import dataclasses
from collections.abc import Sequence
from typing import Self

from gha_toolkit.files import StepSummaryFile


@dataclasses.dataclass(frozen=True, slots=True)
class SummaryTableCell:
    """One cell of a :meth:`ActionSummary.add_table` row.

    Snake_case counterpart of upstream `SummaryTableCell` (`summary.ts:12-30`).
    `data` is the cell's rendered content. `header` selects `<th>` instead of
    `<td>` when `True` (default `False`, i.e. a plain data cell). `colspan`
    and `rowspan` are upstream-typed as strings, not integers -- e.g. `'3'`,
    not `3` -- and are rendered as HTML attributes only when set (default
    `None`, meaning "no `colspan`/`rowspan` attribute at all", not `'1'`).

    A plain `str` is also a valid table cell wherever `SummaryTableCell |
    str` is accepted (see :data:`SummaryTableRow`); it renders as a bare
    `<td>` with no attributes, equivalent to `SummaryTableCell(data=that_str)`.
    """

    data: str
    header: bool = False
    colspan: str | None = None
    rowspan: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class SummaryImageOptions:
    """Optional sizing attributes for :meth:`ActionSummary.add_image`.

    Snake_case counterpart of upstream `SummaryImageOptions`
    (`summary.ts:32-44`). Both fields are upstream-typed as strings holding a
    bare integer pixel count -- e.g. `'32'`, not `32` -- and are rendered as
    HTML attributes on the `<img>` element only when set (default `None`,
    meaning "no `width`/`height` attribute at all").
    """

    width: str | None = None
    height: str | None = None


SummaryTableRow = Sequence[SummaryTableCell | str]
"""One row of :meth:`ActionSummary.add_table`'s `rows` argument.

Snake_case counterpart of upstream `SummaryTableRow` (`summary.ts:9`): a
sequence of cells, each either a :class:`SummaryTableCell` or a bare `str`
(equivalent to a header-less, span-less `SummaryTableCell`).
"""


class ActionSummary:
    """A pure, fluent, in-memory HTML/markdown buffer for a job step summary.

    Every `add_*` method appends a rendered HTML element (or raw text) to an
    internal string buffer and returns `self`, so calls chain:
    `summary.add_heading('Title').add_raw('body', add_eol=True).stringify()`.
    This class has no knowledge of `GITHUB_STEP_SUMMARY` or any other runner
    file -- it never performs I/O and can be constructed and used anywhere.
    :class:`ActionStepSummary` is the file-bound half that flushes an
    instance of this buffer to disk; this class deliberately has no `write`,
    `clear`, or file member of its own.
    """

    def __init__(self) -> None:
        """Initialize an empty buffer.

        The only state this class holds; no I/O happens here or anywhere
        else in this class.
        """
        self._buffer = ''

    def _wrap(
        self,
        tag: str,
        content: str | None,
        attrs: dict[str, str] | None = None,
    ) -> str:
        """Render `content` wrapped in an HTML `tag`, with `attrs` as attributes.

        Parity with upstream's private `wrap()` (`summary.ts:97-115`): each
        `attrs` entry renders as `' key="value"'`, in `attrs`' iteration
        order, immediately after the tag name. When `content` is `None` or
        empty, the result is the void form `<tag attrs>` with no closing
        tag; otherwise it is `<tag attrs>content</tag>`. Every `add_*`
        builder below is defined in terms of this helper plus
        :meth:`add_raw`/:meth:`add_eol`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_raw(self, text: str, *, add_eol: bool = False) -> Self:
        """Append `text` to the buffer verbatim, with no HTML wrapping.

        Parity with upstream `addRaw` (`summary.ts:172-179`). `add_eol` is
        keyword-only (repo convention for boolean parameters); when `True`,
        `os.linesep` is appended after `text` via :meth:`add_eol`. Every
        other `add_*` builder in this class is implemented on top of this
        method.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_eol(self) -> Self:
        """Append the OS end-of-line marker (`os.linesep`) to the buffer.

        Parity with upstream `addEOL` (`summary.ts:181-186`); equivalent to
        `self.add_raw(os.linesep)`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_code_block(self, code: str, lang: str | None = None) -> Self:
        """Append a fenced code block: `<pre lang="...?"><code>code</code></pre>` + EOL.

        Parity with upstream `addCodeBlock` (`summary.ts:196-204`). The
        `lang` attribute is rendered on the outer `<pre>` tag, and only when
        `lang` is given -- e.g. `<pre lang="python"><code>...</code></pre>`;
        with no `lang`, the tag is a bare `<pre><code>...</code></pre>`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_list(self, items: Sequence[str], *, ordered: bool = False) -> Self:
        """Append a list: `<ul>`/`<ol>` of one `<li>` per item, + EOL.

        Parity with upstream `addList` (`summary.ts:214-220`). `ordered` is
        keyword-only (repo convention for boolean parameters); `True`
        renders `<ol>...</ol>`, `False` (default) renders `<ul>...</ul>`.
        Each entry in `items` is wrapped bare, with no attributes:
        `<li>item</li>`, concatenated in order with no separator between
        them, before the whole list plus its own EOL is appended.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_table(self, rows: Sequence[SummaryTableRow]) -> Self:
        """Append an HTML table built from `rows`, + EOL.

        Parity with upstream `addTable` (`summary.ts:228-253`). Renders
        `<table>` containing one `<tr>` per row; each row's cells render in
        order with no separator between them. A bare `str` cell renders as
        `<td>cell</td>`. A :class:`SummaryTableCell` cell renders as
        `<th>` when `header` is `True`, `<td>` otherwise, with `colspan`
        and/or `rowspan` attributes present, in that order, only when the
        cell sets them. Example rendered fragment (for a header row and a
        row with a `rowspan="3"` cell):
        `'<table><tr><th>foo</th>...<td rowspan="3">tall</td></tr>...</table>'`
        followed by `os.linesep`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_details(self, label: str, content: str) -> Self:
        """Append a collapsible section: `<details><summary>label</summary>content</details>` + EOL.

        Parity with upstream `addDetails` (`summary.ts:261-266`); `content`
        is inserted after the `<summary>` element, unwrapped. Example:
        `'<details><summary>open me</summary>content</details>'` followed by
        `os.linesep`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_image(
        self,
        src: str,
        alt: str,
        options: SummaryImageOptions | None = None,
    ) -> Self:
        """Append a void image tag: `<img src="..." alt="..." [width] [height]>` + EOL.

        Parity with upstream `addImage` (`summary.ts:274-284`). Attributes
        render in this fixed order: `src`, `alt`, then `width` and `height`
        from `options`, each present only when `options` sets it (`options`
        itself defaults to `None`, equivalent to neither being set). Example:
        `'<img src="..." alt="..." width="32" height="32">'` followed by
        `os.linesep`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_heading(self, text: str, level: int | str = 1) -> Self:
        """Append a section heading: `<h{level}>text</h{level}>` + EOL.

        Parity with upstream `addHeading` (`summary.ts:292-300`). `level` is
        rendered into the tag name `'h{level}'` (via plain string
        interpolation -- `level` may be an `int` or a `str`) and clamped to
        `h1` whenever the interpolated tag is not exactly one of `'h1'`
        through `'h6'`. This clamp fires for any garbage or out-of-range
        input, not just malformed strings: negative integers (`-5` ->
        `'h-5'`), integers above `6` (`12` -> `'h12'`), `0`, and arbitrary
        non-numeric strings (`'abc'` -> `'habc'`) all fall outside `h1`-`h6`
        and render as `<h1>text</h1>`. Only the exact integers `1` through
        `6` (or their string forms `'1'`-`'6'`) render at their requested
        level.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_separator(self) -> Self:
        """Append a void thematic break: `<hr>` + EOL.

        Parity with upstream `addSeparator` (`summary.ts:306-310`).

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_break(self) -> Self:
        """Append a void line break: `<br>` + EOL.

        Parity with upstream `addBreak` (`summary.ts:316-320`).

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_quote(self, text: str, cite: str | None = None) -> Self:
        """Append a quote: `<blockquote [cite="..."]>text</blockquote>` + EOL.

        Parity with upstream `addQuote` (`summary.ts:329-335`). The `cite`
        attribute is present only when `cite` is given (default `None`,
        meaning no `cite` attribute).

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def add_link(self, text: str, href: str) -> Self:
        """Append a hyperlink: `<a href="...">text</a>` + EOL.

        Parity with upstream `addLink` (`summary.ts:343-346`).

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def stringify(self) -> str:
        """Return the buffer's current contents as a single string.

        Parity with upstream `stringify` (`summary.ts:150-153`). Does not
        clear the buffer -- see :meth:`empty_buffer` for that.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def is_empty_buffer(self) -> bool:
        """Return whether the buffer currently holds no content.

        Parity with upstream `isEmptyBuffer` (`summary.ts:158-161`);
        equivalent to `len(self.stringify()) == 0`.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def empty_buffer(self) -> Self:
        """Clear the buffer's contents and return `self`.

        Parity with upstream `emptyBuffer` (`summary.ts:167-170`). Does not
        touch any file -- this class has none; :class:`ActionStepSummary`
        calls this after a successful :meth:`ActionStepSummary.write` to
        empty the buffer it wraps.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError


class ActionStepSummary:
    """Binds an :class:`ActionSummary` buffer to a `GITHUB_STEP_SUMMARY` file.

    This is the file-bound half of the summary pair: it owns `write()` and
    `clear()`, the two operations upstream's single `Summary` class mixes
    into its buffer methods. `ActionSummary` itself stays a pure buffer with
    no `write`, `clear`, or file member -- that split is the point of this
    module (see the module docstring). Callers build content through the
    bound `buffer` attribute (`step_summary.buffer.add_heading(...)`) and
    flush it to the runner's summary file through this class's own methods.
    """

    def __init__(
        self,
        step_summary_file: StepSummaryFile,
        buffer: ActionSummary | None = None,
    ) -> None:
        """Bind this instance to `step_summary_file`, and to `buffer` if given.

        `buffer` defaults to a freshly constructed, empty
        :class:`ActionSummary` when omitted. Storing both references is the
        entire constructor; no I/O happens until :meth:`write` or
        :meth:`clear` is called.
        """
        self._step_summary_file = step_summary_file
        self.buffer = buffer if buffer is not None else ActionSummary()

    def write(self, *, overwrite: bool = False) -> Self:
        """Flush the bound buffer's contents to the summary file, then empty it.

        Parity with upstream `Summary.write` (`summary.ts:122-129`).
        `overwrite` is keyword-only (repo convention for boolean
        parameters); appends by default, or truncates-then-writes when
        `True` -- delegates to `step_summary_file.write(buffer.stringify(),
        overwrite=overwrite)`, then calls `buffer.empty_buffer()` and
        returns `self`.

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: see
                :meth:`gha_toolkit.files.StepSummaryFile.write`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def clear(self) -> Self:
        """Empty the bound buffer and truncate the summary file to empty.

        Parity with upstream `Summary.clear` (`summary.ts:135-138`), i.e.
        `buffer.empty_buffer()` followed by `write(overwrite=True)`.

        Raises:
            gha_toolkit.exceptions.SummaryAccessError: see
                :meth:`gha_toolkit.files.StepSummaryFile.write`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
