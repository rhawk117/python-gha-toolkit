from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import pytest
from pytest_mock import MockerFixture

from gha_toolkit.sinks import StdoutSink


@dataclass(slots=True)
class WriteRecorder:
    calls: list[str] = field(default_factory=list)

    def write(self, line: str) -> None:
        self.calls.append(line)

    def flush(self) -> None: ...

    def assert_writes(self, expected: Sequence[str]) -> None:
        assert self.calls == list(expected)

    def assert_no_writes(self) -> None:
        assert self.calls == []

    def assert_contains_none_of(self, forbidden: Sequence[str]) -> None:
        joined = ''.join(self.calls)
        for value in forbidden:
            assert value not in joined

    def reset(self) -> None:
        self.calls.clear()


@pytest.fixture
def sink() -> WriteRecorder:
    return WriteRecorder()


@pytest.fixture
def stdout_sink(mocker: MockerFixture) -> WriteRecorder:
    recorder = WriteRecorder()
    mocker.patch('sys.stdout.write', side_effect=recorder.write)
    return recorder


@pytest.fixture
def make_command_sink() -> Callable[[WriteRecorder], StdoutSink]:
    """Factory for a `StdoutSink` bound to a `WriteRecorder` stream."""

    def _make(stream: WriteRecorder) -> StdoutSink:
        return StdoutSink(stream=stream)

    return _make
