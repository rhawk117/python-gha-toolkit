"""Markers shared by every test module."""

import pytest

pending = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason='signature defined, implementation pending',
)

requires_posix = pytest.mark.skipif(
    "sys.platform == 'win32'",
    reason='posix path semantics',
)

requires_windows = pytest.mark.skipif(
    "sys.platform != 'win32'",
    reason='win32 path semantics',
)

serial = pytest.mark.xdist_group(name='serial')
