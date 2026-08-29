"""Runtime construction and binding fixtures."""

from collections.abc import Callable

import pytest

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
