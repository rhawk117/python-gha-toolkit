"""Workflow input access, ported from core.test.ts's `getInput`/`getBooleanInput`/
`getMultilineInput` cases.

Every stub builds an `EnvInputs` directly over a `GithubEnvironment` bound to
`test_environ` (the merged runner + toolkit fixture dotenv vars, via
`make_environment`), then calls the stock accessor the upstream test
exercises.
"""

from collections.abc import Callable

import pytest
from tests.markers import pending

from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.exceptions import InputParseError, MissingInputError
from gha_toolkit.inputs import EnvInputs


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('name', 'required', 'trim', 'expected'),
    [
        pytest.param('my input', False, True, 'val', id='non_required'),
        pytest.param('my input', True, True, 'val', id='required'),
        pytest.param('My InPuT', False, True, 'val', id='case_insensitive'),
        pytest.param(
            'special chars_\'\t"\\',
            False,
            True,
            '\'\t"\\ response',
            id='special_characters',
        ),
        pytest.param(
            'multiple spaces variable',
            False,
            True,
            'I have multiple spaces',
            id='multiple_spaces',
        ),
        pytest.param(
            'with trailing whitespace', False, True, 'some val', id='trims_by_default'
        ),
        pytest.param(
            'with trailing whitespace',
            False,
            True,
            'some val',
            id='trims_when_explicitly_true',
        ),
        pytest.param(
            'with trailing whitespace',
            False,
            False,
            '  some val  ',
            id='does_not_trim_when_false',
        ),
    ],
)
def test_get_input_returns_the_expected_string(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
    name: str,
    *,
    required: bool,
    trim: bool,
    expected: str,
) -> None:
    """upstream: core.test.ts: 'getInput gets non-required input'
    upstream: core.test.ts: 'getInput gets required input'
    upstream: core.test.ts: 'getInput is case insensitive'
    upstream: core.test.ts: 'getInput handles special characters'
    upstream: core.test.ts: 'getInput handles multiple spaces'
    upstream: core.test.ts: 'getInput trims whitespace by default'
    upstream: core.test.ts: 'getInput trims whitespace when option is explicitly true'
    upstream: core.test.ts: 'getInput does not trim whitespace when option is false'
    """
    inputs = make_inputs(make_environment())
    assert inputs.get_string(name, required=required, trim=trim) == expected


@pytest.mark.parity
@pending
def test_get_input_throws_on_missing_required_input(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getInput throws on missing required input'"""
    inputs = make_inputs(make_environment())
    with pytest.raises(MissingInputError):
        inputs.get_string('missing', required=True)


@pytest.mark.parity
@pending
def test_get_input_does_not_throw_on_missing_non_required_input(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getInput does not throw on missing non-required input'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_string('missing', required=False) == ''


@pytest.mark.parity
@pending
def test_get_input_gets_non_required_boolean_input(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getInput gets non-required boolean input'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_boolean('boolean input') is True


@pytest.mark.parity
@pending
def test_get_boolean_input_gets_required_input(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getInput gets required input' (boolean overload)"""
    inputs = make_inputs(make_environment())
    assert inputs.get_boolean('boolean input', required=True) is True


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        pytest.param('boolean input true1', True, id='true1'),
        pytest.param('boolean input true2', True, id='true2'),
        pytest.param('boolean input true3', True, id='true3'),
        pytest.param('boolean input false1', False, id='false1'),
        pytest.param('boolean input false2', False, id='false2'),
        pytest.param('boolean input false3', False, id='false3'),
    ],
)
def test_get_boolean_input_handles_every_yaml_boolean_literal(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
    name: str,
    *,
    expected: bool,
) -> None:
    """upstream: core.test.ts: 'getBooleanInput handles boolean input'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_boolean(name) is expected


@pytest.mark.extension
@pending
def test_get_boolean_input_handles_wrong_boolean_input(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getBooleanInput handles wrong boolean input'

    Deviation of record (gha_toolkit.inputs module docstring): upstream raises
    a bare `TypeError` here; this port raises the typed `InputParseError`
    instead, so this is ported as an extension rather than a byte-identical
    parity case.
    """
    inputs = make_inputs(make_environment())
    with pytest.raises(InputParseError):
        inputs.get_boolean('wrong boolean input')


@pytest.mark.parity
@pending
def test_get_multiline_input_works(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput works'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_multiline('my input list') == ['val1', 'val2', 'val3']


@pytest.mark.parity
@pending
def test_get_multiline_input_trims_whitespace_by_default(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput trims whitespace by default'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_multiline('list with trailing whitespace') == ['val1', 'val2']


@pytest.mark.parity
@pending
def test_get_multiline_input_trims_whitespace_when_option_explicitly_true(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput trims whitespace when option is explicitly true'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_multiline('list with trailing whitespace', trim=True) == [
        'val1',
        'val2',
    ]


@pytest.mark.parity
@pending
def test_get_multiline_input_does_not_trim_whitespace_when_option_false(
    make_inputs: Callable[[ProcessEnvironment], EnvInputs],
    make_environment: Callable[..., ProcessEnvironment],
) -> None:
    """upstream: core.test.ts: 'getMultilineInput does not trim whitespace when option is false'"""
    inputs = make_inputs(make_environment())
    assert inputs.get_multiline('list with trailing whitespace', trim=False) == [
        '  val1  ',
        '  val2  ',
        '  ',
    ]
