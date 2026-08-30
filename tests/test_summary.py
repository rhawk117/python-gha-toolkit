"""The job step summary pair (`ActionSummary` buffer + `ActionStepSummary` file
binding), ported from summary.test.ts.

File-backed cases bind a `StepSummaryFile` to a real `tmp_path` file through
`GithubEnvironment`; buffer-only cases (`stringify`, `is_empty_buffer`) build
a bare `ActionSummary` with no file at all, matching upstream's split between
`summary.write()`-flushed assertions and pure in-memory buffer assertions.
"""

from collections.abc import Mapping
from pathlib import Path

import pytest
from tests.markers import pending

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.exceptions import SummaryAccessError
from gha_toolkit.files import StepSummaryFile
from gha_toolkit.summary import (
    ActionStepSummary,
    ActionSummary,
    SummaryImageOptions,
    SummaryTableCell,
)

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


def _step_summary(test_environ: Mapping[str, str], tmp_path: Path) -> ActionStepSummary:
    summary_path = tmp_path / 'test-summary.md'
    summary_path.write_text('', encoding='utf-8')
    environ = {**test_environ, 'GITHUB_STEP_SUMMARY': str(summary_path)}
    environment = GithubEnvironment(dict(environ))
    return ActionStepSummary(StepSummaryFile('GITHUB_STEP_SUMMARY', environment))


@pytest.mark.parity
@pending
def test_throws_if_summary_env_var_is_undefined(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: summary.test.ts: 'throws if summary env var is undefined'"""
    environ = {**test_environ, 'GITHUB_STEP_SUMMARY': ''}
    environment = GithubEnvironment(dict(environ))
    step_summary = ActionStepSummary(
        StepSummaryFile('GITHUB_STEP_SUMMARY', environment)
    )
    step_summary.buffer.add_raw(TEXT)
    with pytest.raises(SummaryAccessError):
        step_summary.write()


@pytest.mark.parity
@pending
def test_throws_if_summary_file_does_not_exist(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'throws if summary file does not exist'"""
    missing_path = tmp_path / 'missing-summary.md'
    environ = {**test_environ, 'GITHUB_STEP_SUMMARY': str(missing_path)}
    environment = GithubEnvironment(dict(environ))
    step_summary = ActionStepSummary(
        StepSummaryFile('GITHUB_STEP_SUMMARY', environment)
    )
    step_summary.buffer.add_raw(TEXT)
    with pytest.raises(SummaryAccessError):
        step_summary.write()


@pytest.mark.parity
@pending
def test_appends_text_to_summary_file(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'appends text to summary file'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT)
    step_summary.write()


@pytest.mark.parity
@pending
def test_overwrites_text_to_summary_file(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'overwrites text to summary file'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT)
    step_summary.write(overwrite=True)


@pytest.mark.parity
@pending
def test_appends_text_with_eol_to_summary_file(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'appends text with EOL to summary file'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT, add_eol=True)
    step_summary.write()


@pytest.mark.parity
@pending
def test_chains_appends_text_to_summary_file(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'chains appends text to summary file'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT).add_raw(TEXT).add_raw(TEXT)
    step_summary.write()


@pytest.mark.parity
@pending
def test_empties_buffer_after_write(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'empties buffer after write'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT)
    step_summary.write()
    assert step_summary.buffer.is_empty_buffer() is True


@pytest.mark.parity
@pending
def test_returns_summary_buffer_as_string() -> None:
    """upstream: summary.test.ts: 'returns summary buffer as string'"""
    buffer = ActionSummary()
    buffer.add_raw(TEXT)
    assert buffer.stringify() == TEXT


@pytest.mark.parity
@pending
def test_returns_correct_values_for_is_empty_buffer() -> None:
    """upstream: summary.test.ts: 'return correct values for isEmptyBuffer'"""
    buffer = ActionSummary()
    buffer.add_raw(TEXT)
    assert buffer.is_empty_buffer() is False
    buffer.empty_buffer()
    assert buffer.is_empty_buffer() is True


@pytest.mark.parity
@pending
def test_clears_a_buffer_and_summary_file(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'clears a buffer and summary file'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.clear()
    assert step_summary.buffer.is_empty_buffer() is True


@pytest.mark.parity
@pending
def test_adds_eol(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds EOL'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_raw(TEXT).add_eol()
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_code_block_without_language(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a code block without language'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_code_block(CODE)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_code_block_with_a_language(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a code block with a language'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_code_block(CODE, 'go')
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_an_unordered_list(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an unordered list'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_list(LIST)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_an_ordered_list(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds an ordered list'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_list(LIST, ordered=True)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_table(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a table'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_table(TABLE)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_details_element(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a details element'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_details('open me', '\U0001f389 surprise')
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_an_image_with_alt_text(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an image with alt text'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_image('https://github.com/actions.png', 'actions logo')
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_an_image_with_custom_dimensions(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an image with custom dimensions'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_image(
        'https://github.com/actions.png',
        'actions logo',
        SummaryImageOptions(width='32', height='32'),
    )
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_an_image_with_custom_dimensions_again(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds an image with custom dimensions' (second occurrence)

    Upstream declares this exact same test name twice; ported as two distinct
    Python stubs to preserve the 1:1 `it(...)` count.
    """
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_image(
        'https://github.com/actions.png',
        'actions logo',
        SummaryImageOptions(width='32', height='32'),
    )
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_headings_h1_through_h6(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds headings h1...h6'"""
    step_summary = _step_summary(test_environ, tmp_path)
    for level in (1, 2, 3, 4, 5, 6):
        step_summary.buffer.add_heading('heading', level)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_h1_if_heading_level_not_specified(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds h1 if heading level not specified'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_heading('heading')
    step_summary.write()


@pytest.mark.parity
@pending
def test_uses_h1_if_heading_level_is_garbage_or_out_of_range(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'uses h1 if heading level is garbage or out of range'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_heading('heading', 'foobar').add_heading(
        'heading', 1337
    ).add_heading('heading', -1)
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_separator(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a separator'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_separator()
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_break(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a break'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_break()
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_quote(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a quote'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_quote('Where the world builds software')
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_quote_with_citation(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: summary.test.ts: 'adds a quote with citation'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_quote(
        'Where the world builds software', 'https://github.com/about'
    )
    step_summary.write()


@pytest.mark.parity
@pending
def test_adds_a_link_with_href(test_environ: Mapping[str, str], tmp_path: Path) -> None:
    """upstream: summary.test.ts: 'adds a link with href'"""
    step_summary = _step_summary(test_environ, tmp_path)
    step_summary.buffer.add_link('GitHub', 'https://github.com/')
    step_summary.write()
