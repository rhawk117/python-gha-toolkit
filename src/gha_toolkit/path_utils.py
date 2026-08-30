"""Pure path-string transforms between posix, win32, and platform-native form.

Ported from ``.original/toolkit/packages/core/src/path-utils.ts``. All three
functions are pure string transforms operating on their `pth` argument
alone -- none of them touch the filesystem, inspect the host, or resolve a
path against a base directory; the only host-dependent behavior in this
module is :func:`to_platform_path`'s use of `os.sep` as its substitution
target.

This is an interface-only module: every function below raises
``NotImplementedError``.
"""


def to_posix_path(pth: str) -> str:
    """Return `pth` with every backslash (`\\\\`) replaced by a forward slash (`/`).

    Parity with upstream `toPosixPath` (`path-utils.ts`,
    `pth.replace(/[\\\\]/g, '/')`): a global substitution, every backslash
    in `pth` is replaced, not just leading or path-separator-position ones.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def to_win32_path(pth: str) -> str:
    """Return `pth` with every forward slash (`/`) replaced by a backslash (`\\\\`).

    Parity with upstream `toWin32Path` (`path-utils.ts`,
    `pth.replace(/[/]/g, '\\\\')`): a global substitution, every forward
    slash in `pth` is replaced.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


def to_platform_path(pth: str) -> str:
    """Return `pth` with every `/` and `\\\\` replaced by `os.sep`.

    Parity with upstream `toPlatformPath` (`path-utils.ts`,
    `pth.replace(/[/\\\\]/g, path.sep)`): a global substitution over both
    separator characters, replaced with whatever `os.sep` is on the host
    this function runs on (`'\\\\'` on Windows, `'/'` elsewhere).

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError
