"""Workflow input access, ported from core.test.ts's `getInput`/`getBooleanInput`/
`getMultilineInput` cases.

Every stub builds an `ActionsInputs` directly over a `GithubEnvironment` bound
to `test_environ` (the merged runner + toolkit fixture dotenv vars), then
calls the stock accessor the upstream test exercises.
"""

from collections.abc import Mapping

import pytest
from tests.markers import pending

from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.exceptions import InputParseError, MissingInputError
from gha_toolkit.inputs import EnvInputs


@pytest.mark.parity
@pending
def test_get_input_gets_non_required_input(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput gets non-required input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('my input') == 'val'


@pytest.mark.parity
@pending
def test_get_input_gets_required_input(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput gets required input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('my input', required=True) == 'val'


@pytest.mark.parity
@pending
def test_get_input_throws_on_missing_required_input(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getInput throws on missing required input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    with pytest.raises(MissingInputError):
        inputs.get_string('missing', required=True)


@pytest.mark.parity
@pending
def test_get_input_does_not_throw_on_missing_non_required_input(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getInput does not throw on missing non-required input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('missing', required=False) == ''


@pytest.mark.parity
@pending
def test_get_input_is_case_insensitive(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput is case insensitive'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('My InPuT') == 'val'


@pytest.mark.parity
@pending
def test_get_input_handles_special_characters(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput handles special characters'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('special chars_\'\t"\\') == '\'\t"\\ response'


@pytest.mark.parity
@pending
def test_get_input_handles_multiple_spaces(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput handles multiple spaces'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('multiple spaces variable') == 'I have multiple spaces'


@pytest.mark.parity
@pending
def test_get_input_trims_whitespace_by_default(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput trims whitespace by default'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('with trailing whitespace') == 'some val'


@pytest.mark.parity
@pending
def test_get_input_trims_whitespace_when_option_explicitly_true(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getInput trims whitespace when option is explicitly true'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('with trailing whitespace', trim=True) == 'some val'


@pytest.mark.parity
@pending
def test_get_input_does_not_trim_whitespace_when_option_false(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getInput does not trim whitespace when option is false'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_string('with trailing whitespace', trim=False) == '  some val  '


@pytest.mark.parity
@pending
def test_get_input_gets_non_required_boolean_input(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getInput gets non-required boolean input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_boolean('boolean input') is True


@pytest.mark.parity
@pending
def test_get_boolean_input_gets_required_input(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getInput gets required input' (boolean overload)"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_boolean('boolean input', required=True) is True


@pytest.mark.parity
@pending
def test_get_boolean_input_handles_boolean_input(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getBooleanInput handles boolean input'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_boolean('boolean input true1') is True
    assert inputs.get_boolean('boolean input true2') is True
    assert inputs.get_boolean('boolean input true3') is True
    assert inputs.get_boolean('boolean input false1') is False
    assert inputs.get_boolean('boolean input false2') is False
    assert inputs.get_boolean('boolean input false3') is False


@pytest.mark.extension
@pending
def test_get_boolean_input_handles_wrong_boolean_input(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getBooleanInput handles wrong boolean input'

    Deviation of record (gha_toolkit.inputs module docstring): upstream raises
    a bare `TypeError` here; this port raises the typed `InputParseError`
    instead, so this is ported as an extension rather than a byte-identical
    parity case.
    """
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    with pytest.raises(InputParseError):
        inputs.get_boolean('wrong boolean input')


@pytest.mark.parity
@pending
def test_get_multiline_input_works(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getMultilineInput works'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_multiline('my input list') == ['val1', 'val2', 'val3']


@pytest.mark.parity
@pending
def test_get_multiline_input_trims_whitespace_by_default(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput trims whitespace by default'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_multiline('list with trailing whitespace') == ['val1', 'val2']


@pytest.mark.parity
@pending
def test_get_multiline_input_trims_whitespace_when_option_explicitly_true(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput trims whitespace when option is explicitly true'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_multiline('list with trailing whitespace', trim=True) == [
        'val1',
        'val2',
    ]


@pytest.mark.parity
@pending
def test_get_multiline_input_does_not_trim_whitespace_when_option_false(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput does not trim whitespace when option is false'"""
    inputs = EnvInputs(ProcessEnvironment(dict(test_environ)))
    assert inputs.get_multiline('list with trailing whitespace', trim=False) == [
        '  val1  ',
        '  val2  ',
        '  ',
    ]
