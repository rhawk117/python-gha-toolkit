"""`GITHUB_ENV`/`GITHUB_OUTPUT`/`GITHUB_STATE` file commands, ported from
core.test.ts's `exportVariable`/`setOutput`/`saveState` cases.

Three groups per command family: the legacy stdout-fallback tests (ported as
extension-marked inversions asserting `MissingRunnerFileError`, since the
runner disabled the `::set-env`/`::set-output`/`::save-state` stdout fallback
in 2022 -- see `gha_toolkit.files`'s module docstring), the parity tests
(writing the delimiter-framed heredoc block to a real file), and the
delimiter-injection tests (security-marked).
"""

import os
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.fixtures import MakeEnvFile, MakeEnvironment, MakeOutput, MakeState
from tests.fixtures.runtime import FROZEN_DELIMITER
from tests.markers import pending

from gha_toolkit.commands import OutputValue
from gha_toolkit.exceptions import DelimiterInjectionError, MissingRunnerFileError

# -- exportVariable -----------------------------------------------------


@pytest.mark.extension
@pending
@pytest.mark.parametrize(
    ('key', 'value'),
    [
        pytest.param('my var', 'var val', id='baseline'),
        pytest.param(
            'special char var \r\n,:', 'special val', id='escapes_variable_names'
        ),
        pytest.param('my var2', 'var val\r\n', id='escapes_variable_values'),
        pytest.param('my var', True, id='boolean_inputs'),
        pytest.param('my var', 5, id='number_inputs'),
    ],
)
def test_legacy_export_variable_raises_when_env_file_is_missing(
    make_environment: MakeEnvironment,
    make_env_file: MakeEnvFile,
    key: str,
    value: OutputValue,
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable produces the correct command and sets the env'
    upstream: core.test.ts: 'legacy exportVariable escapes variable names'
    upstream: core.test.ts: 'legacy exportVariable escapes variable values'
    upstream: core.test.ts: 'legacy exportVariable handles boolean inputs'
    upstream: core.test.ts: 'legacy exportVariable handles number inputs'

    Decision of record (gha_toolkit.files module docstring): a missing
    `GITHUB_ENV` raises `MissingRunnerFileError` instead of falling back to
    the removed `::set-env` stdout command.
    """
    environment = make_environment({'GITHUB_ENV': ''})
    env_file = make_env_file(environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set(key, value)


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('value', 'expected_value'),
    [
        pytest.param('var val', 'var val', id='string'),
        pytest.param(True, 'true', id='boolean'),
        pytest.param(5, '5', id='number'),
    ],
)
def test_export_variable_writes_heredoc_block_for_value_shape(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_env_file: MakeEnvFile,
    delimiter: Callable[[], str],
    value: OutputValue,
    expected_value: str,
) -> None:
    """upstream: core.test.ts: 'exportVariable produces the correct command and sets the env'
    upstream: core.test.ts: 'exportVariable handles boolean inputs'
    upstream: core.test.ts: 'exportVariable handles number inputs'
    """
    env_path = runner_file_path('env')
    environment = make_environment({'GITHUB_ENV': str(env_path)})
    env_file = make_env_file(environment, delimiter)
    env_file.set('my var', value)
    expected = (
        f'my var<<{FROZEN_DELIMITER}{os.linesep}'
        f'{expected_value}{os.linesep}'
        f'{FROZEN_DELIMITER}{os.linesep}'
    )
    assert env_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_export_variable_sets_the_environment_for_the_current_process(
    make_environment: MakeEnvironment,
) -> None:
    """upstream: core.test.ts: 'exportVariable produces the correct command and sets the env'

    Environment round-trip half of the upstream case; the heredoc write is
    covered by `test_export_variable_writes_heredoc_block_for_value_shape`.
    """
    environment = make_environment()
    environment.set('my var', 'var val')
    assert environment.get('my var') == 'var val'


@pytest.mark.security
@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('key', 'value'),
    [
        pytest.param(
            'my var', f'good stuff {FROZEN_DELIMITER} bad stuff', id='in_value'
        ),
        pytest.param(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test', id='in_name'),
    ],
)
def test_export_variable_rejects_forged_delimiter(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_env_file: MakeEnvFile,
    delimiter: Callable[[], str],
    key: str,
    value: str,
) -> None:
    """upstream: core.test.ts: 'exportVariable does not allow delimiter as value'
    upstream: core.test.ts: 'exportVariable does not allow delimiter as name'
    """
    env_path = runner_file_path('env')
    environment = make_environment({'GITHUB_ENV': str(env_path)})
    env_file = make_env_file(environment, delimiter)
    with pytest.raises(DelimiterInjectionError):
        env_file.set(key, value)


# -- setOutput ------------------------------------------------------------


@pytest.mark.extension
@pending
@pytest.mark.parametrize(
    'value',
    [
        pytest.param('some value', id='string'),
        pytest.param(False, id='boolean'),
        pytest.param(1.01, id='number'),
    ],
)
def test_legacy_set_output_raises_when_output_file_is_missing(
    make_environment: MakeEnvironment, make_output: MakeOutput, value: OutputValue
) -> None:
    """upstream: core.test.ts: 'legacy setOutput produces the correct command'
    upstream: core.test.ts: 'legacy setOutput handles bools'
    upstream: core.test.ts: 'legacy setOutput handles numbers'
    """
    environment = make_environment({'GITHUB_OUTPUT': ''})
    output = make_output(environment)
    with pytest.raises(MissingRunnerFileError):
        output.set('some output', value)


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('value', 'expected_value'),
    [
        pytest.param('out val', 'out val', id='string'),
        pytest.param(True, 'true', id='boolean'),
        pytest.param(5, '5', id='number'),
    ],
)
def test_set_output_writes_heredoc_block_for_value_shape(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_output: MakeOutput,
    delimiter: Callable[[], str],
    value: OutputValue,
    expected_value: str,
) -> None:
    """upstream: core.test.ts: 'setOutput produces the correct command and sets the output'
    upstream: core.test.ts: 'setOutput handles boolean inputs'
    upstream: core.test.ts: 'setOutput handles number inputs'
    """
    output_path = runner_file_path('output')
    environment = make_environment({'GITHUB_OUTPUT': str(output_path)})
    output = make_output(environment, delimiter)
    output.set('my out', value)
    expected = (
        f'my out<<{FROZEN_DELIMITER}{os.linesep}'
        f'{expected_value}{os.linesep}'
        f'{FROZEN_DELIMITER}{os.linesep}'
    )
    assert output_path.read_text(encoding='utf-8') == expected


@pytest.mark.security
@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('key', 'value'),
    [
        pytest.param(
            'my out', f'good stuff {FROZEN_DELIMITER} bad stuff', id='in_value'
        ),
        pytest.param(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test', id='in_name'),
    ],
)
def test_set_output_rejects_forged_delimiter(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_output: MakeOutput,
    delimiter: Callable[[], str],
    key: str,
    value: str,
) -> None:
    """upstream: core.test.ts: 'setOutput does not allow delimiter as value'
    upstream: core.test.ts: 'setOutput does not allow delimiter as name'
    """
    output_path = runner_file_path('output')
    environment = make_environment({'GITHUB_OUTPUT': str(output_path)})
    output = make_output(environment, delimiter)
    with pytest.raises(DelimiterInjectionError):
        output.set(key, value)


# -- saveState --------------------------------------------------------------


@pytest.mark.extension
@pending
@pytest.mark.parametrize(
    'value',
    [
        pytest.param('some value', id='string'),
        pytest.param(1, id='number'),
        pytest.param(True, id='boolean'),
    ],
)
def test_legacy_save_state_raises_when_state_file_is_missing(
    make_environment: MakeEnvironment, make_state: MakeState, value: OutputValue
) -> None:
    """upstream: core.test.ts: 'legacy saveState produces the correct command'
    upstream: core.test.ts: 'legacy saveState handles numbers'
    upstream: core.test.ts: 'legacy saveState handles bools'
    """
    environment = make_environment({'GITHUB_STATE': ''})
    state = make_state(environment)
    with pytest.raises(MissingRunnerFileError):
        state.save('state_1', value)


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('value', 'expected_value'),
    [
        pytest.param('out val', 'out val', id='string'),
        pytest.param(True, 'true', id='boolean'),
        pytest.param(5, '5', id='number'),
    ],
)
def test_save_state_writes_heredoc_block_for_value_shape(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_state: MakeState,
    delimiter: Callable[[], str],
    value: OutputValue,
    expected_value: str,
) -> None:
    """upstream: core.test.ts: 'saveState produces the correct command and saves the state'
    upstream: core.test.ts: 'saveState handles boolean inputs'
    upstream: core.test.ts: 'saveState handles number inputs'
    """
    state_path = runner_file_path('state')
    environment = make_environment({'GITHUB_STATE': str(state_path)})
    state = make_state(environment, delimiter)
    state.save('my state', value)
    expected = (
        f'my state<<{FROZEN_DELIMITER}{os.linesep}'
        f'{expected_value}{os.linesep}'
        f'{FROZEN_DELIMITER}{os.linesep}'
    )
    assert state_path.read_text(encoding='utf-8') == expected


@pytest.mark.security
@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('key', 'value'),
    [
        pytest.param(
            'my state', f'good stuff {FROZEN_DELIMITER} bad stuff', id='in_value'
        ),
        pytest.param(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test', id='in_name'),
    ],
)
def test_save_state_rejects_forged_delimiter(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_state: MakeState,
    delimiter: Callable[[], str],
    key: str,
    value: str,
) -> None:
    """upstream: core.test.ts: 'saveState does not allow delimiter as value'
    upstream: core.test.ts: 'saveState does not allow delimiter as name'
    """
    state_path = runner_file_path('state')
    environment = make_environment({'GITHUB_STATE': str(state_path)})
    state = make_state(environment, delimiter)
    with pytest.raises(DelimiterInjectionError):
        state.save(key, value)
