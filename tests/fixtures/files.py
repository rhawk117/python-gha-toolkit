"""Runner-file construction fixtures: HeredocFile/PathListFile/SummaryFile and the
StepOutput/StepState/RunnerPaths services built directly on top of them.

Every factory here owns a construction call the AC-1 grep forbids inside
test_*.py; a test builds the `GithubEnvironment` it wants (via
`make_environment`/`make_oidc_environment`) and hands it to the factory that
matches the service under test.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import ActionsFiles, HeredocFile, PathListFile, SummaryFile
from gha_toolkit.services import RunnerPaths, StepOutput, StepState


@pytest.fixture
def runner_file_path(tmp_path: Path) -> Callable[[str], Path]:
    """Write an empty runner-file under `tmp_path` and return its path."""

    def _make(name: str) -> Path:
        path = tmp_path / name
        path.write_text('', encoding='utf-8')
        return path

    return _make


@pytest.fixture
def make_env_file() -> Callable[..., HeredocFile]:
    def _make(
        environment: GithubEnvironment,
        delimiter: Callable[[], str] | None = None,
        *,
        env_var: str = 'GITHUB_ENV',
    ) -> HeredocFile:
        if delimiter is None:
            return HeredocFile(env_var, environment)
        return HeredocFile(env_var, environment, delimiter)

    return _make


@pytest.fixture
def make_output(
    make_env_file: Callable[..., HeredocFile],
) -> Callable[..., StepOutput]:
    def _make(
        environment: GithubEnvironment, delimiter: Callable[[], str] | None = None
    ) -> StepOutput:
        return StepOutput(
            make_env_file(environment, delimiter, env_var='GITHUB_OUTPUT')
        )

    return _make


@pytest.fixture
def make_state(make_env_file: Callable[..., HeredocFile]) -> Callable[..., StepState]:
    def _make(
        environment: GithubEnvironment, delimiter: Callable[[], str] | None = None
    ) -> StepState:
        env_file = make_env_file(environment, delimiter, env_var='GITHUB_STATE')
        return StepState(env_file, environment)

    return _make


@pytest.fixture
def make_paths() -> Callable[[GithubEnvironment], RunnerPaths]:
    def _make(environment: GithubEnvironment) -> RunnerPaths:
        return RunnerPaths(PathListFile('GITHUB_PATH', environment), environment)

    return _make


@pytest.fixture
def make_actions_files() -> Callable[
    [GithubEnvironment, Callable[[], str]], ActionsFiles
]:
    def _make(
        environment: GithubEnvironment, delimiter: Callable[[], str]
    ) -> ActionsFiles:
        return ActionsFiles(
            env=HeredocFile('GITHUB_ENV', environment, delimiter),
            output=HeredocFile('GITHUB_OUTPUT', environment, delimiter),
            state=HeredocFile('GITHUB_STATE', environment, delimiter),
            path=PathListFile('GITHUB_PATH', environment),
            step_summary=SummaryFile('GITHUB_STEP_SUMMARY', environment),
        )

    return _make
