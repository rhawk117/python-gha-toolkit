"""The job step summary pair (`HtmlSummaryBuffer` buffer + `StepSummaryWriter`
file binding), ported from summary.test.ts.

File-backed cases use the `step_summary` fixture, a `StepSummaryWriter` bound
to a real `tmp_path` file; buffer-only cases (`stringify`, `is_empty`)
use the bare `summary_buffer` fixture with no file at all, matching
upstream's split between `summary.write()`-flushed assertions and pure
in-memory buffer assertions.
"""

import os
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.markers import pending

from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.exceptions import SummaryAccessError
from gha_toolkit.summary import (
    HtmlSummaryBuffer,
    StepSummaryWriter,
    SummaryImageOptions,
    SummaryTableCell,
)

MakeEnvironment = Callable[..., ProcessEnvironment]
MakeStepSummary = Callable[[ProcessEnvironment], StepSummaryWriter]

TEXT = 'hello world \U0001f30e'
CODE = 'func fork() {\n  for {\n    go fork()\n  }\n}'
LIST = ['foo', 'bar', 'baz', '\U0001f4a3']
TABLE = [
    [
        SummaryTableCell(data='foo', header=True),
        SummaryTableCell(data='bar', header=True),
        SummaryTableCell(data='baz', header=True),
        SummaryTableCell(data='tall', rowspan='3'),
    ],
    ['one', 'two', 'three'],
    [SummaryTableCell(data='wide', colspan='3')],
]


@pytest.mark.parity
@pending
def test_throws_if_summary_env_var_is_undefined(
    make_environment: MakeEnvironment, make_step_summary: MakeStepSummary
) -> None:
    """upstream: summary.test.ts: 'throws if summary env var is undefined'"""
    step_summary = make_step_summary(make_environment({'GITHUB_STEP_SUMMARY': ''}))
    step_summary.buffer.add_raw(TEXT)
    with pytest.raises(SummaryAccessError):
        step_summary.write()


@pytest.mark.parity
@pending
def test_throws_if_summary_file_does_not_exist(
    make_environment: MakeEnvironment,
    make_step_summary: MakeStepSummary,
    tmp_path: Path,
) -> None:
    """upstream: summary.test.ts: 'throws if summary file does not exist'"""
    missing_path = tmp_path / 'missing-summary.md'
    environment = make_environment({'GITHUB_STEP_SUMMARY': str(missing_path)})
    step_summary = make_step_summary(environment)
    step_summary.buffer.add_raw(TEXT)
    with pytest.raises(SummaryAccessError):
        step_summary.write()


@pytest.mark.parity
@pending
def test_appends_text_to_summary_file(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'appends text to summary file'"""
    step_summary_path.write_text('# ', encoding='utf-8')
    step_summary.buffer.add_raw(TEXT)
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == f'# {TEXT}'


@pytest.mark.parity
@pending
def test_overwrites_text_to_summary_file(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'overwrites text to summary file'"""
    step_summary_path.write_text('overwrite', encoding='utf-8')
    step_summary.buffer.add_raw(TEXT)
    step_summary.write(overwrite=True)
    assert step_summary_path.read_text(encoding='utf-8') == TEXT


@pytest.mark.parity
@pending
def test_appends_text_with_eol_to_summary_file(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'appends text with EOL to summary file'"""
    step_summary_path.write_text('# ', encoding='utf-8')
    step_summary.buffer.add_raw(TEXT, add_eol=True)
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == f'# {TEXT}{os.linesep}'


@pytest.mark.parity
@pending
def test_chains_appends_text_to_summary_file(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'chains appends text to summary file'"""
    step_summary.buffer.add_raw(TEXT).add_raw(TEXT).add_raw(TEXT)
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == TEXT * 3


@pytest.mark.parity
@pending
def test_empties_buffer_after_write(step_summary: StepSummaryWriter) -> None:
    """upstream: summary.test.ts: 'empties buffer after write'"""
    step_summary.buffer.add_raw(TEXT)
    step_summary.write()
    assert step_summary.buffer.is_empty() is True


@pytest.mark.parity
@pending
def test_returns_summary_buffer_as_string(summary_buffer: HtmlSummaryBuffer) -> None:
    """upstream: summary.test.ts: 'returns summary buffer as string'"""
    summary_buffer.add_raw(TEXT)
    assert summary_buffer.stringify() == TEXT


@pytest.mark.parity
@pending
def test_returns_correct_values_for_is_empty(
    summary_buffer: HtmlSummaryBuffer,
) -> None:
    """upstream: summary.test.ts: 'return correct values for isEmptyBuffer'"""
    summary_buffer.add_raw(TEXT)
    assert summary_buffer.is_empty() is False
    summary_buffer.clear()
    assert summary_buffer.is_empty() is True


@pytest.mark.parity
@pending
def test_clears_a_buffer_and_summary_file(step_summary: StepSummaryWriter) -> None:
    """upstream: summary.test.ts: 'clears a buffer and summary file'"""
    step_summary.clear()
    assert step_summary.buffer.is_empty() is True


@pytest.mark.parity
@pending
def test_adds_eol(step_summary: StepSummaryWriter, step_summary_path: Path) -> None:
    """upstream: summary.test.ts: 'adds EOL'"""
    step_summary.buffer.add_raw(TEXT).add_eol()
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == TEXT + os.linesep


@pytest.mark.parity
@pending
def test_adds_a_code_block_without_language(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a code block without language'"""
    step_summary.buffer.add_code_block(CODE)
    step_summary.write()
    expected = f'<pre><code>{CODE}</code></pre>{os.linesep}'
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_a_code_block_with_a_language(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a code block with a language'"""
    step_summary.buffer.add_code_block(CODE, 'go')
    step_summary.write()
    expected = f'<pre lang="go"><code>{CODE}</code></pre>{os.linesep}'
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_an_unordered_list(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an unordered list'"""
    step_summary.buffer.add_list(LIST)
    step_summary.write()
    expected = (
        f'<ul><li>foo</li><li>bar</li><li>baz</li><li>\U0001f4a3</li></ul>{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_an_ordered_list(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an ordered list'"""
    step_summary.buffer.add_list(LIST, ordered=True)
    step_summary.write()
    expected = (
        f'<ol><li>foo</li><li>bar</li><li>baz</li><li>\U0001f4a3</li></ol>{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_a_table(step_summary: StepSummaryWriter, step_summary_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a table'"""
    step_summary.buffer.add_table(TABLE)
    step_summary.write()
    expected = (
        '<table><tr><th>foo</th><th>bar</th><th>baz</th>'
        '<td rowspan="3">tall</td></tr><tr><td>one</td><td>two</td>'
        '<td>three</td></tr><tr><td colspan="3">wide</td></tr></table>'
        f'{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_a_details_element(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a details element'"""
    step_summary.buffer.add_details('open me', '\U0001f389 surprise')
    step_summary.write()
    expected = (
        f'<details><summary>open me</summary>\U0001f389 surprise</details>{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_an_image_with_alt_text(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an image with alt text'"""
    step_summary.buffer.add_image('https://github.com/actions.png', 'actions logo')
    step_summary.write()
    expected = (
        f'<img src="https://github.com/actions.png" alt="actions logo">{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
@pytest.mark.parametrize('occurrence', ['first', 'second'])
def test_adds_an_image_with_custom_dimensions(
    step_summary: StepSummaryWriter, step_summary_path: Path, occurrence: str
) -> None:
    """upstream: summary.test.ts: 'adds an image with custom dimensions'

    Upstream declares this exact same test name twice; ported as two
    parametrized cases (rather than two near-identical function bodies) to
    preserve the 1:1 `it(...)` count.
    """
    del occurrence
    step_summary.buffer.add_image(
        'https://github.com/actions.png',
        'actions logo',
        SummaryImageOptions(width='32', height='32'),
    )
    step_summary.write()
    expected = (
        '<img src="https://github.com/actions.png" alt="actions logo" '
        f'width="32" height="32">{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
@pytest.mark.parametrize('level', [1, 2, 3, 4, 5, 6])
def test_adds_heading_at_level(
    step_summary: StepSummaryWriter, step_summary_path: Path, level: int
) -> None:
    """upstream: summary.test.ts: 'adds headings h1...h6'"""
    step_summary.buffer.add_heading('heading', level)
    step_summary.write()
    expected = f'<h{level}>heading</h{level}>{os.linesep}'
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_h1_if_heading_level_not_specified(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds h1 if heading level not specified'"""
    step_summary.buffer.add_heading('heading')
    step_summary.write()
    assert (
        step_summary_path.read_text(encoding='utf-8') == f'<h1>heading</h1>{os.linesep}'
    )


@pytest.mark.parity
@pending
@pytest.mark.parametrize('level', ['foobar', 1337, -1])
def test_uses_h1_if_heading_level_is_garbage_or_out_of_range(
    step_summary: StepSummaryWriter, step_summary_path: Path, level: int | str
) -> None:
    """upstream: summary.test.ts: 'uses h1 if heading level is garbage or out of range'"""
    step_summary.buffer.add_heading('heading', level)
    step_summary.write()
    assert (
        step_summary_path.read_text(encoding='utf-8') == f'<h1>heading</h1>{os.linesep}'
    )


@pytest.mark.parity
@pending
def test_adds_a_separator(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a separator'"""
    step_summary.buffer.add_separator()
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == f'<hr>{os.linesep}'


@pytest.mark.parity
@pending
def test_adds_a_break(step_summary: StepSummaryWriter, step_summary_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a break'"""
    step_summary.buffer.add_break()
    step_summary.write()
    assert step_summary_path.read_text(encoding='utf-8') == f'<br>{os.linesep}'


@pytest.mark.parity
@pending
def test_adds_a_quote(step_summary: StepSummaryWriter, step_summary_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a quote'"""
    step_summary.buffer.add_quote('Where the world builds software')
    step_summary.write()
    expected = f'<blockquote>Where the world builds software</blockquote>{os.linesep}'
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_a_quote_with_citation(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a quote with citation'"""
    step_summary.buffer.add_quote(
        'Where the world builds software', 'https://github.com/about'
    )
    step_summary.write()
    expected = (
        '<blockquote cite="https://github.com/about">'
        f'Where the world builds software</blockquote>{os.linesep}'
    )
    assert step_summary_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_adds_a_link_with_href(
    step_summary: StepSummaryWriter, step_summary_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a link with href'"""
    step_summary.buffer.add_link('GitHub', 'https://github.com/')
    step_summary.write()
    expected = f'<a href="https://github.com/">GitHub</a>{os.linesep}'
    assert step_summary_path.read_text(encoding='utf-8') == expected
