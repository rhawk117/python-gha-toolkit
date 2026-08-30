"""`GITHUB_ENV`/`GITHUB_OUTPUT`/`GITHUB_STATE` file commands, ported from
core.test.ts's `exportVariable`/`setOutput`/`saveState` cases.

Three groups per command family: the legacy stdout-fallback tests (ported as
extension-marked inversions asserting `MissingRunnerFileError`, since the
runner disabled the `::set-env`/`::set-output`/`::save-state` stdout fallback
in 2022 -- see `gha_toolkit.files`'s module docstring), the parity tests
(writing the delimiter-framed heredoc block to a real file), and the
delimiter-injection tests (security-marked).
"""

from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from tests.fixtures.runtime import FROZEN_DELIMITER
from tests.markers import pending

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.exceptions import DelimiterInjectionError, MissingRunnerFileError
from gha_toolkit.files import KeyValueFile
from gha_toolkit.services import ActionsOutput, ActionsState


def _environment_with_file(
    test_environ: Mapping[str, str], env_var: str, file_path: Path
) -> GithubEnvironment:
    file_path.write_text('', encoding='utf-8')
    environ = {**test_environ, env_var: str(file_path)}
    return GithubEnvironment(dict(environ))


def _environment_missing_file(
    test_environ: Mapping[str, str], env_var: str
) -> GithubEnvironment:
    environ = {**test_environ, env_var: ''}
    return GithubEnvironment(dict(environ))


# -- exportVariable -----------------------------------------------------


@pytest.mark.extension
@pending
def test_legacy_export_variable_produces_command_and_sets_env(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable produces the correct command and sets the env'

    Decision of record (gha_toolkit.files module docstring): a missing
    `GITHUB_ENV` raises `MissingRunnerFileError` instead of falling back to
    the removed `::set-env` stdout command.
    """
    environment = _environment_missing_file(test_environ, 'GITHUB_ENV')
    env_file = KeyValueFile('GITHUB_ENV', environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set('my var', 'var val')


@pytest.mark.extension
@pending
def test_legacy_export_variable_escapes_variable_names(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable escapes variable names'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_ENV')
    env_file = KeyValueFile('GITHUB_ENV', environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set('special char var \r\n,:', 'special val')


@pytest.mark.extension
@pending
def test_legacy_export_variable_escapes_variable_values(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable escapes variable values'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_ENV')
    env_file = KeyValueFile('GITHUB_ENV', environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set('my var2', 'var val\r\n')


@pytest.mark.extension
@pending
def test_legacy_export_variable_handles_boolean_inputs(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable handles boolean inputs'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_ENV')
    env_file = KeyValueFile('GITHUB_ENV', environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set('my var', True)


@pytest.mark.extension
@pending
def test_legacy_export_variable_handles_number_inputs(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy exportVariable handles number inputs'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_ENV')
    env_file = KeyValueFile('GITHUB_ENV', environment)
    with pytest.raises(MissingRunnerFileError):
        env_file.set('my var', 5)


@pytest.mark.parity
@pending
def test_export_variable_produces_command_and_sets_env(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'exportVariable produces the correct command and sets the env'"""
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    environment.set('my var', 'var val')
    assert environment.get('my var') == 'var val'
    env_file = KeyValueFile('GITHUB_ENV', environment, delimiter)
    env_file.set('my var', 'var val')
    expected = f'my var<<{FROZEN_DELIMITER}\nvar val\n{FROZEN_DELIMITER}\n'
    assert env_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_export_variable_handles_boolean_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'exportVariable handles boolean inputs'"""
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    env_file = KeyValueFile('GITHUB_ENV', environment, delimiter)
    env_file.set('my var', True)
    expected = f'my var<<{FROZEN_DELIMITER}\ntrue\n{FROZEN_DELIMITER}\n'
    assert env_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_export_variable_handles_number_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'exportVariable handles number inputs'"""
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    env_file = KeyValueFile('GITHUB_ENV', environment, delimiter)
    env_file.set('my var', 5)
    expected = f'my var<<{FROZEN_DELIMITER}\n5\n{FROZEN_DELIMITER}\n'
    assert env_path.read_text(encoding='utf-8') == expected


@pytest.mark.security
@pytest.mark.parity
@pending
def test_export_variable_rejects_delimiter_in_value(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'exportVariable does not allow delimiter as value'"""
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    env_file = KeyValueFile('GITHUB_ENV', environment, delimiter)
    with pytest.raises(DelimiterInjectionError):
        env_file.set('my var', f'good stuff {FROZEN_DELIMITER} bad stuff')


@pytest.mark.security
@pytest.mark.parity
@pending
def test_export_variable_rejects_delimiter_in_name(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'exportVariable does not allow delimiter as name'"""
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    env_file = KeyValueFile('GITHUB_ENV', environment, delimiter)
    with pytest.raises(DelimiterInjectionError):
        env_file.set(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test')


# -- setOutput ------------------------------------------------------------


@pytest.mark.extension
@pending
def test_legacy_set_output_produces_command(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy setOutput produces the correct command'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_OUTPUT')
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment))
    with pytest.raises(MissingRunnerFileError):
        output.set('some output', 'some value')


@pytest.mark.extension
@pending
def test_legacy_set_output_handles_bools(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy setOutput handles bools'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_OUTPUT')
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment))
    with pytest.raises(MissingRunnerFileError):
        output.set('some output', False)


@pytest.mark.extension
@pending
def test_legacy_set_output_handles_numbers(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy setOutput handles numbers'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_OUTPUT')
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment))
    with pytest.raises(MissingRunnerFileError):
        output.set('some output', 1.01)


@pytest.mark.parity
@pending
def test_set_output_produces_command_and_sets_output(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'setOutput produces the correct command and sets the output'"""
    output_path = tmp_path / 'output'
    environment = _environment_with_file(test_environ, 'GITHUB_OUTPUT', output_path)
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment, delimiter))
    output.set('my out', 'out val')
    expected = f'my out<<{FROZEN_DELIMITER}\nout val\n{FROZEN_DELIMITER}\n'
    assert output_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_set_output_handles_boolean_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'setOutput handles boolean inputs'"""
    output_path = tmp_path / 'output'
    environment = _environment_with_file(test_environ, 'GITHUB_OUTPUT', output_path)
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment, delimiter))
    output.set('my out', True)
    expected = f'my out<<{FROZEN_DELIMITER}\ntrue\n{FROZEN_DELIMITER}\n'
    assert output_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_set_output_handles_number_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'setOutput handles number inputs'"""
    output_path = tmp_path / 'output'
    environment = _environment_with_file(test_environ, 'GITHUB_OUTPUT', output_path)
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment, delimiter))
    output.set('my out', 5)
    expected = f'my out<<{FROZEN_DELIMITER}\n5\n{FROZEN_DELIMITER}\n'
    assert output_path.read_text(encoding='utf-8') == expected


@pytest.mark.security
@pytest.mark.parity
@pending
def test_set_output_rejects_delimiter_in_value(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'setOutput does not allow delimiter as value'"""
    output_path = tmp_path / 'output'
    environment = _environment_with_file(test_environ, 'GITHUB_OUTPUT', output_path)
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment, delimiter))
    with pytest.raises(DelimiterInjectionError):
        output.set('my out', f'good stuff {FROZEN_DELIMITER} bad stuff')


@pytest.mark.security
@pytest.mark.parity
@pending
def test_set_output_rejects_delimiter_in_name(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'setOutput does not allow delimiter as name'"""
    output_path = tmp_path / 'output'
    environment = _environment_with_file(test_environ, 'GITHUB_OUTPUT', output_path)
    output = ActionsOutput(KeyValueFile('GITHUB_OUTPUT', environment, delimiter))
    with pytest.raises(DelimiterInjectionError):
        output.set(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test')


# -- saveState --------------------------------------------------------------


@pytest.mark.extension
@pending
def test_legacy_save_state_produces_command(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy saveState produces the correct command'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_STATE')
    state = ActionsState(KeyValueFile('GITHUB_STATE', environment), environment)
    with pytest.raises(MissingRunnerFileError):
        state.save('state_1', 'some value')


@pytest.mark.extension
@pending
def test_legacy_save_state_handles_numbers(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy saveState handles numbers'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_STATE')
    state = ActionsState(KeyValueFile('GITHUB_STATE', environment), environment)
    with pytest.raises(MissingRunnerFileError):
        state.save('state_1', 1)


@pytest.mark.extension
@pending
def test_legacy_save_state_handles_bools(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'legacy saveState handles bools'"""
    environment = _environment_missing_file(test_environ, 'GITHUB_STATE')
    state = ActionsState(KeyValueFile('GITHUB_STATE', environment), environment)
    with pytest.raises(MissingRunnerFileError):
        state.save('state_1', True)


@pytest.mark.parity
@pending
def test_save_state_produces_command_and_saves_state(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'saveState produces the correct command and saves the state'"""
    state_path = tmp_path / 'state'
    environment = _environment_with_file(test_environ, 'GITHUB_STATE', state_path)
    state = ActionsState(
        KeyValueFile('GITHUB_STATE', environment, delimiter), environment
    )
    state.save('my state', 'out val')
    expected = f'my state<<{FROZEN_DELIMITER}\nout val\n{FROZEN_DELIMITER}\n'
    assert state_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_save_state_handles_boolean_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'saveState handles boolean inputs'"""
    state_path = tmp_path / 'state'
    environment = _environment_with_file(test_environ, 'GITHUB_STATE', state_path)
    state = ActionsState(
        KeyValueFile('GITHUB_STATE', environment, delimiter), environment
    )
    state.save('my state', True)
    expected = f'my state<<{FROZEN_DELIMITER}\ntrue\n{FROZEN_DELIMITER}\n'
    assert state_path.read_text(encoding='utf-8') == expected


@pytest.mark.parity
@pending
def test_save_state_handles_number_inputs(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'saveState handles number inputs'"""
    state_path = tmp_path / 'state'
    environment = _environment_with_file(test_environ, 'GITHUB_STATE', state_path)
    state = ActionsState(
        KeyValueFile('GITHUB_STATE', environment, delimiter), environment
    )
    state.save('my state', 5)
    expected = f'my state<<{FROZEN_DELIMITER}\n5\n{FROZEN_DELIMITER}\n'
    assert state_path.read_text(encoding='utf-8') == expected


@pytest.mark.security
@pytest.mark.parity
@pending
def test_save_state_rejects_delimiter_in_value(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'saveState does not allow delimiter as value'"""
    state_path = tmp_path / 'state'
    environment = _environment_with_file(test_environ, 'GITHUB_STATE', state_path)
    state = ActionsState(
        KeyValueFile('GITHUB_STATE', environment, delimiter), environment
    )
    with pytest.raises(DelimiterInjectionError):
        state.save('my state', f'good stuff {FROZEN_DELIMITER} bad stuff')


@pytest.mark.security
@pytest.mark.parity
@pending
def test_save_state_rejects_delimiter_in_name(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """upstream: core.test.ts: 'saveState does not allow delimiter as name'"""
    state_path = tmp_path / 'state'
    environment = _environment_with_file(test_environ, 'GITHUB_STATE', state_path)
    state = ActionsState(
        KeyValueFile('GITHUB_STATE', environment, delimiter), environment
    )
    with pytest.raises(DelimiterInjectionError):
        state.save(f'good stuff {FROZEN_DELIMITER} bad stuff', 'test')
