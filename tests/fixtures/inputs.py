"""`EnvInputs` construction fixture."""

from collections.abc import Callable

import pytest

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.inputs import EnvInputs


@pytest.fixture
def make_inputs() -> Callable[[GithubEnvironment], EnvInputs]:
    def _make(environment: GithubEnvironment) -> EnvInputs:
        return EnvInputs(environment)

    return _make
