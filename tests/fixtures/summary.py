"""Job-step-summary construction fixtures: `HtmlSummaryBuffer` and `StepSummaryWriter`."""

from collections.abc import Callable
from pathlib import Path

import pytest

from gha_toolkit.environment import GithubEnvironment, ProcessEnvironment
from gha_toolkit.files import SummaryFile
from gha_toolkit.summary import HtmlSummaryBuffer, StepSummaryWriter


@pytest.fixture
def summary_buffer() -> HtmlSummaryBuffer:
    return HtmlSummaryBuffer()


@pytest.fixture
def make_step_summary() -> Callable[[GithubEnvironment], StepSummaryWriter]:
    def _make(environment: GithubEnvironment) -> StepSummaryWriter:
        return StepSummaryWriter(
            SummaryFile('GITHUB_STEP_SUMMARY', environment), HtmlSummaryBuffer()
        )

    return _make


@pytest.fixture
def step_summary_path(runner_file_path: Callable[[str], Path]) -> Path:
    """The real, empty `GITHUB_STEP_SUMMARY` file `step_summary` is bound to --
    exposed separately so a test can read back what `write()` wrote.
    """
    return runner_file_path('test-summary.md')


@pytest.fixture
def step_summary(
    make_environment: Callable[..., ProcessEnvironment],
    step_summary_path: Path,
    make_step_summary: Callable[[GithubEnvironment], StepSummaryWriter],
) -> StepSummaryWriter:
    """A `StepSummaryWriter` bound to a real, empty `GITHUB_STEP_SUMMARY` file --
    the shape every summary test but the two undefined/missing-file cases needs.
    """
    environment = make_environment({'GITHUB_STEP_SUMMARY': str(step_summary_path)})
    return make_step_summary(environment)
