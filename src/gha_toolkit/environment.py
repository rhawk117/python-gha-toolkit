"""The process-environment seam every other subsystem reads runner state through.

:class:`GithubEnvironment` replaces direct ``os.environ`` access everywhere else in
this package. Binding through one typed seam, rather than reading ``os.environ``
ad hoc, is what lets tests substitute a fake mapping instead of monkeypatching the
real process environment, and is the single place a future implementation enforces
"no stdout fallback" for missing runner state.

Ported from ``.original/toolkit/packages/core/src/core.ts``'s ``exportVariable`` /
``process.env`` reads scattered across that file; this module consolidates them.
Upstream's ``exportVariable`` also prepends to ``process.env.PATH`` with the
platform path separator as a side effect of setting ``PATH`` specifically -- that
PATH-prepending policy is a services-layer concern (``ActionsPaths``, a later task)
and does not belong on this seam, which only binds and writes environment entries.

This is an interface-only module: every method below raises ``NotImplementedError``.
Only the constructor, which stores its arguments, is real.
"""

import os
from collections.abc import MutableMapping


class GithubEnvironment:
    """Typed get/set access over a process-environment-shaped mapping.

    Wraps ``os.environ`` by default; accepting an injectable mapping is what lets
    tests bind a fake environ (a plain ``dict``) instead of monkeypatching the real
    process environment. Every other subsystem that needs an environment variable
    -- runner file paths, workflow inputs, webhook context -- reads it through an
    instance of this class rather than importing ``os`` directly.
    """

    def __init__(self, environ: MutableMapping[str, str] | None = None) -> None:
        """Bind this instance to `environ`, defaulting to the real `os.environ`.

        Construction only stores a reference; no environment variables are read
        or validated until :meth:`get`, :meth:`require`, or :meth:`set` is called.
        """
        self._environ = environ if environ is not None else os.environ

    def get(self, name: str, default: str | None = None) -> str | None:
        """Return the value bound to `name`, or `default` if it is unset or empty.

        Mirrors upstream's `??? process.env[name] || ''` pattern generalized to a
        caller-supplied default rather than a hardcoded empty string.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def require(self, name: str) -> str:
        """Return the value bound to `name`, raising if it is unset or empty.

        This is the generic missing-value seam beneath every runner-file and
        required-input contract in this package: callers that need a
        gha_toolkit-typed error -- :class:`gha_toolkit.exceptions.MissingRunnerFileError`
        for a runner file variable, :class:`gha_toolkit.exceptions.MissingInputError`
        for a required workflow input -- catch whatever this raises and re-raise
        their own typed exception around it.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def set(self, name: str, value: str) -> None:
        """Write `value` into the bound environment mapping under `name`.

        Mirrors the `process.env[name] = value` write inside upstream's
        `exportVariable`, minus that function's `PATH`-specific prepending
        behavior -- see the module docstring for where that policy lives instead.

        Raises:
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
