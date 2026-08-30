"""Pure path-string transforms, ported from path-utils.test.ts's three
`describe.each`-style data tables (`#toPosixPath`, `#toWin32Path`,
`#toPlatformPath`).
"""

import os

import pytest
from tests.markers import pending

from gha_toolkit.path_utils import to_platform_path, to_posix_path, to_win32_path

# upstream: path-utils.test.ts: '#toPosixPath'
POSIX_CASES = [
    pytest.param('', '', id='empty string'),
    pytest.param('foo', 'foo', id='single value'),
    pytest.param('foo/bar/baz', 'foo/bar/baz', id='with posix relative'),
    pytest.param('/foo/bar/baz', '/foo/bar/baz', id='with posix absolute'),
    pytest.param('foo\\bar\\baz', 'foo/bar/baz', id='with win32 relative'),
    pytest.param('\\foo\\bar\\baz', '/foo/bar/baz', id='with win32 absolute'),
    pytest.param('\\foo/bar/baz', '/foo/bar/baz', id='with a mix'),
]

# upstream: path-utils.test.ts: '#toWin32Path'
WIN32_CASES = [
    pytest.param('', '', id='empty string'),
    pytest.param('foo', 'foo', id='single value'),
    pytest.param('foo/bar/baz', 'foo\\bar\\baz', id='with posix relative'),
    pytest.param('/foo/bar/baz', '\\foo\\bar\\baz', id='with posix absolute'),
    pytest.param('foo\\bar\\baz', 'foo\\bar\\baz', id='with win32 relative'),
    pytest.param('\\foo\\bar\\baz', '\\foo\\bar\\baz', id='with win32 absolute'),
    pytest.param('\\foo/bar\\baz', '\\foo\\bar\\baz', id='with a mix'),
]

# upstream: path-utils.test.ts: '#toPlatformPath' -- expected values are
# built from `os.sep` (rather than a literal separator) so this stub passes
# on whichever host platform it collects on, parity with upstream's use of
# `path.join(path.sep, ...)` for the same purpose.
_RELATIVE = f'foo{os.sep}bar{os.sep}baz'
_ABSOLUTE = f'{os.sep}foo{os.sep}bar{os.sep}baz'

PLATFORM_CASES = [
    pytest.param('', '', id='empty string'),
    pytest.param('foo', 'foo', id='single value'),
    pytest.param('foo/bar/baz', _RELATIVE, id='with posix relative'),
    pytest.param('/foo/bar/baz', _ABSOLUTE, id='with posix absolute'),
    pytest.param('foo\\bar\\baz', _RELATIVE, id='with win32 relative'),
    pytest.param('\\foo\\bar\\baz', _ABSOLUTE, id='with win32 absolute'),
    pytest.param('\\foo/bar\\baz', _ABSOLUTE, id='with a mix'),
]


@pytest.mark.parity
@pending
@pytest.mark.parametrize(('pth', 'expected'), POSIX_CASES)
def test_to_posix_path(pth: str, expected: str) -> None:
    assert to_posix_path(pth) == expected


@pytest.mark.parity
@pending
@pytest.mark.parametrize(('pth', 'expected'), WIN32_CASES)
def test_to_win32_path(pth: str, expected: str) -> None:
    assert to_win32_path(pth) == expected


@pytest.mark.parity
@pending
@pytest.mark.parametrize(('pth', 'expected'), PLATFORM_CASES)
def test_to_platform_path(pth: str, expected: str) -> None:
    assert to_platform_path(pth) == expected
