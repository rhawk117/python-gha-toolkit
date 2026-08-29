import os
from pathlib import Path

import pytest
from hypothesis import HealthCheck, Verbosity, settings


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).parents[1].resolve()


pytest_plugins = (
    'fixtures.environment',
    'fixtures.runtime',
    'fixtures.sink_recorder',
)


settings.register_profile(
    'dev',
    max_examples=50,
    deadline=200,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    'ci',
    max_examples=500,
    deadline=None,
    derandomize=False,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    'debug',
    max_examples=10,
    deadline=None,
    verbosity=Verbosity.verbose,
)

settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'dev'))
