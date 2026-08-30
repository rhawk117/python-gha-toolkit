"""`GITHUB_PATH` prepending and `GITHUB_STATE` reads, ported from core.test.ts's
`addPath`/`getState` cases.
"""

import os
from collections.abc import Mapping
from pathlib import Path

import pytest
from tests.markers import pending

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.exceptions import MissingRunnerFileError
from gha_toolkit.files import KeyValueFile, PathFile
from gha_toolkit.services import ActionsPaths, ActionsState


@pytest.mark.parity
@pending
def test_prepend_path_produces_commands_and_sets_env(
    test_environ: Mapping[str, str], tmp_path: Path
) -> None:
    """upstream: core.test.ts: 'prependPath produces the correct commands and sets the env'"""
    path_file_path = tmp_path / 'path'
    path_file_path.write_text('', encoding='utf-8')
    environ = {**test_environ, 'GITHUB_PATH': str(path_file_path)}
    environment = GithubEnvironment(dict(environ))
    paths = ActionsPaths(PathFile('GITHUB_PATH', environment), environment)
    paths.add('myPath')
    assert environment.get('PATH') == f'myPath{os.pathsep}path1{os.pathsep}path2'
    assert path_file_path.read_text(encoding='utf-8') == f'myPath{os.linesep}'


@pytest.mark.extension
@pending
def test_legacy_prepend_path_produces_commands_and_sets_env(
    test_environ: Mapping[str, str],
) -> None:
    """upstream: core.test.ts: 'legacy prependPath produces the correct commands and sets the env'

    Decision of record (gha_toolkit.files module docstring): a missing
    `GITHUB_PATH` raises `MissingRunnerFileError` instead of falling back to
    the removed `::add-path` stdout command.
    """
    environ = {**test_environ, 'GITHUB_PATH': ''}
    environment = GithubEnvironment(dict(environ))
    paths = ActionsPaths(PathFile('GITHUB_PATH', environment), environment)
    with pytest.raises(MissingRunnerFileError):
        paths.add('myPath')


@pytest.mark.parity
@pending
def test_get_state_gets_wrapper_action_state(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'getState gets wrapper action state'"""
    environment = GithubEnvironment(dict(test_environ))
    state = ActionsState(KeyValueFile('GITHUB_STATE', environment), environment)
    assert state.get('TEST_1') == 'state_val'
