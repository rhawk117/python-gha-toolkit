"""`WorkflowLogger` construction fixture."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.logger import WorkflowLogger
from gha_toolkit.sinks import StdoutSink

if TYPE_CHECKING:
    from tests.fixtures.sink_recorder import WriteRecorder


@pytest.fixture
def make_logger(
    make_command_sink: Callable[[WriteRecorder], StdoutSink],
) -> Callable[[WriteRecorder, GithubEnvironment], WorkflowLogger]:
    def _make(stream: WriteRecorder, environment: GithubEnvironment) -> WorkflowLogger:
        return WorkflowLogger(
            sink=make_command_sink(stream), stream=stream, environment=environment
        )

    return _make
