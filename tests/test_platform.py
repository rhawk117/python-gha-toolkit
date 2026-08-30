"""Host platform detail lookup, ported from platform.test.ts.

`gha_toolkit.platform.get_details` is `async def`; the repo has no
`pytest-asyncio` dependency, so each stub drives the coroutine synchronously
through `asyncio.run` rather than declaring an `async def` test function.
"""

import asyncio

import pytest
from tests.markers import pending

from gha_toolkit import platform


@pytest.mark.parity
@pending
def test_returns_the_platform_info() -> None:
    """upstream: platform.test.ts: 'returns the platform info'"""
    details = asyncio.run(platform.get_details())
    assert isinstance(details.name, str)
    assert isinstance(details.platform, str)
    assert isinstance(details.arch, str)
    assert isinstance(details.version, str)
    assert isinstance(details.is_windows, bool)
    assert isinstance(details.is_macos, bool)
    assert isinstance(details.is_linux, bool)


@pytest.mark.parity
@pending
def test_returns_the_platform_info_with_the_correct_name() -> None:
    """upstream: platform.test.ts: 'returns the platform info with the correct name'"""
    details = asyncio.run(platform.get_details())
    assert details.platform == platform.platform
    assert details.is_windows == platform.is_windows
    assert details.is_macos == platform.is_macos
    assert details.is_linux == platform.is_linux
