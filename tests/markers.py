"""Markers shared by every test module."""

import pytest

pending = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason='signature defined, implementation pending',
)
