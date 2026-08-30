"""`GITHUB_PATH` prepending and `GITHUB_STATE` reads, ported from core.test.ts's
`addPath`/`getState` cases.
"""

import os
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.markers import pending

from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.exceptions import MissingRunnerFileError
from gha_toolkit.services import RunnerPaths, StepState

MakeEnvironment = Callable[..., ProcessEnvironment]


@pytest.mark.parity
@pending
def test_prepend_path_produces_commands_and_sets_env(
    make_environment: MakeEnvironment,
    runner_file_path: Callable[[str], Path],
    make_paths: Callable[[ProcessEnvironment], RunnerPaths],
) -> None:
    """upstream: core.test.ts: 'prependPath produces the correct commands and sets the env'"""
    path_file_path = runner_file_path('path')
    environment = make_environment({'GITHUB_PATH': str(path_file_path)})
    paths = make_paths(environment)
    paths.add('myPath')
    assert environment.get('PATH') == f'myPath{os.pathsep}path1{os.pathsep}path2'
    assert path_file_path.read_text(encoding='utf-8') == f'myPath{os.linesep}'


@pytest.mark.extension
@pending
def test_legacy_prepend_path_produces_commands_and_sets_env(
    make_environment: MakeEnvironment,
    make_paths: Callable[[ProcessEnvironment], RunnerPaths],
) -> None:
    """upstream: core.test.ts: 'legacy prependPath produces the correct commands and sets the env'

    Decision of record (gha_toolkit.files module docstring): a missing
    `GITHUB_PATH` raises `MissingRunnerFileError` instead of falling back to
    the removed `::add-path` stdout command.
    """
    environment = make_environment({'GITHUB_PATH': ''})
    paths = make_paths(environment)
    with pytest.raises(MissingRunnerFileError):
        paths.add('myPath')


@pytest.mark.parity
@pending
def test_get_state_gets_wrapper_action_state(
    make_environment: MakeEnvironment,
    make_state: Callable[[ProcessEnvironment], StepState],
) -> None:
    """upstream: core.test.ts: 'getState gets wrapper action state'"""
    environment = make_environment()
    state = make_state(environment)
    assert state.get('TEST_1') == 'state_val'
