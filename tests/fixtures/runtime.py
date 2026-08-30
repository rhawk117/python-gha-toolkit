"""Runtime construction and binding fixtures."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import RunnerFiles
from gha_toolkit.inputs import EnvInputs
from gha_toolkit.logger import WorkflowLogger
from gha_toolkit.oidc import HttpOidcClient
from gha_toolkit.runtime import ActionsRuntime
from gha_toolkit.services import RunnerPaths, StepOutput, StepState
from gha_toolkit.summary import HtmlSummaryBuffer, StepSummaryWriter

if TYPE_CHECKING:
    from tests.fixtures.oidc import TestTokenTransport
    from tests.fixtures.sink_recorder import WriteRecorder

FROZEN_UUID = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d'
FROZEN_DELIMITER = f'ghadelimiter_{FROZEN_UUID}'


@pytest.fixture
def delimiter() -> Callable[[], str]:
    return lambda: FROZEN_DELIMITER


@pytest.fixture
def counting_delimiter() -> Callable[[], str]:
    counter = iter(range(1_000_000))

    def _fixture() -> str:
        return f'ghadelimiter_{next(counter):08d}'

    return _fixture


@pytest.fixture
def make_runtime(
    make_logger: Callable[[WriteRecorder, GithubEnvironment], WorkflowLogger],
    make_runner_files: Callable[[GithubEnvironment, Callable[[], str]], RunnerFiles],
    make_inputs: Callable[[GithubEnvironment], EnvInputs],
    make_oidc_client: Callable[
        [TestTokenTransport, GithubEnvironment, WorkflowLogger], HttpOidcClient
    ],
) -> Callable[
    [GithubEnvironment, WriteRecorder, Callable[[], str], TestTokenTransport],
    ActionsRuntime,
]:
    """Compose a full `ActionsRuntime` from already-constructed services.

    Every call below is a plain constructor storing its arguments -- none of
    them raise -- so building this runtime never itself triggers the pending
    xfail; only calling a method on one of its services does.
    """

    def _make(
        environment: GithubEnvironment,
        stream: WriteRecorder,
        delimiter: Callable[[], str],
        token_transport: TestTokenTransport,
    ) -> ActionsRuntime:
        logger = make_logger(stream, environment)
        files = make_runner_files(environment, delimiter)
        return ActionsRuntime(
            inputs=make_inputs(environment),
            logger=logger,
            output=StepOutput(files.output),
            state=StepState(files.state, environment),
            paths=RunnerPaths(files.path, environment),
            files=files,
            environment=environment,
            step_summary=StepSummaryWriter(files.step_summary, HtmlSummaryBuffer()),
            oidc=make_oidc_client(token_transport, environment, logger),
        )

    return _make
