"""Host platform identification, plus async OS name/version lookup.

Ported from ``.original/toolkit/packages/core/src/platform.ts``. Upstream
exposes four synchronous module-level constants (`platform`, `arch`,
`isWindows`, `isMacOS`, `isLinux`) computed once from Node's `os.platform()`
/ `os.arch()`, plus one async function (`getDetails`) that shells out to an
OS-specific command for the human-readable name and version. This module
keeps that split: the module-level values below are real, eagerly computed
at import time (there is nothing to stub -- they are a plain platform
lookup, not process-spanning behavior), while :func:`get_details` -- the one
member that shells out to a subprocess -- is the interface stub.

Naming note: this module is `gha_toolkit.platform`, and it defines a
module-level attribute also named `platform` (mirroring upstream's `export
const platform`). Importing the standard library `platform` module as bare
`import platform` from inside this file would be shadowed by that
attribute; if a future implementation of :func:`get_details` needs the
standard library module (e.g. `platform.machine()`), it must alias the
import, e.g. `import platform as _stdlib_platform`, exactly as the
docstring here does when referring to it.

Value mapping, decisions of record:
  - `platform` is `sys.platform` verbatim. For the three platforms this
    package targets, `sys.platform` already matches upstream's Node
    `os.platform()` values byte-for-byte: `'win32'` on Windows, `'darwin'`
    on macOS, `'linux'` on Linux -- so no translation table is needed to
    keep parity with upstream's `'win32'`/`'darwin'`/`'linux'` constants.
  - `arch` is the standard library `platform.machine()` value verbatim
    (e.g. `'x86_64'`, `'AMD64'`, `'aarch64'`), deliberately NOT translated
    to Node's `os.arch()` vocabulary (`'x64'`, `'arm64'`, `'ia32'`, ...).
    This is a documented deviation from upstream, scoped to `arch` only --
    `platform.machine()`'s value set is large and platform-dependent enough
    that a translation table is out of scope for this interface-only task.
  - `is_windows` / `is_macos` / `is_linux` are `platform == 'win32'` /
    `platform == 'darwin'` / `platform == 'linux'` respectively, mirroring
    upstream's `isWindows`/`isMacOS`/`isLinux` (`platform.ts`, near the
    bottom of the file).

This is an interface-only module: :func:`get_details` raises
``NotImplementedError``. The module-level values and :class:`PlatformDetails`
(a pure data definition) are real.
"""

import dataclasses
import platform as _stdlib_platform
import sys

platform: str = sys.platform
"""This host's platform name, `sys.platform` verbatim (`'win32'`, `'darwin'`, `'linux'`, ...)."""

arch: str = _stdlib_platform.machine()
"""This host's machine architecture, `platform.machine()` verbatim (e.g. `'x86_64'`)."""

is_windows: bool = platform == 'win32'
"""Whether this host's `platform` is `'win32'`."""

is_macos: bool = platform == 'darwin'
"""Whether this host's `platform` is `'darwin'`."""

is_linux: bool = platform == 'linux'
"""Whether this host's `platform` is `'linux'`."""


@dataclasses.dataclass(frozen=True, slots=True)
class PlatformDetails:
    """The full platform description :func:`get_details` returns.

    Snake_case counterpart of upstream `getDetails`'s inline return type
    (`platform.ts`, `getDetails`'s signature and body). `name` and `version`
    are gathered from an OS-specific subprocess call (see
    :func:`get_details`); the remaining five fields mirror this module's
    own top-level `platform` / `arch` / `is_windows` / `is_macos` /
    `is_linux` values for the host `get_details` was called on.
    """

    name: str
    platform: str
    arch: str
    version: str
    is_windows: bool
    is_macos: bool
    is_linux: bool


async def get_details() -> PlatformDetails:
    """Gather this host's full :class:`PlatformDetails`, including OS name/version.

    Parity with upstream `getDetails` (`platform.ts`): `platform`, `arch`,
    `is_windows`, `is_macos`, `is_linux` are copied from this module's own
    top-level values; `name` and `version` are gathered by running one
    OS-specific command as an async subprocess (mirroring upstream's
    `@actions/exec` calls) and parsing its output:

      - Windows (`is_windows`): two PowerShell `Get-CimInstance
        -ClassName Win32_OperatingSystem` invocations, one reading `.Caption`
        for `name`, one reading `.Version` for `version`
        (`platform.ts`, `getWindowsInfo`).
      - macOS (`is_macos`): `sw_vers`, with `name` parsed from its
        `ProductName:` line and `version` from its `ProductVersion:` line
        (`platform.ts`, `getMacOsInfo`).
      - Linux (otherwise): `lsb_release -i -r -s`, with `name` and `version`
        taken from the command's first two output lines respectively
        (`platform.ts`, `getLinuxInfo`).

    Running the lookup as an async subprocess (rather than a blocking
    `subprocess.run`) is the decision of record for this port: it keeps a
    caller's event loop unblocked for the duration of the external command.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError
