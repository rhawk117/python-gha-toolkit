"""gha_toolkit: a Python port of @actions/core, the GitHub Actions toolkit core package.

This package defines a typed, interface-first surface for writing workflow
commands, reading inputs, managing outputs and state, emitting log annotations,
and interacting with the job summary and OIDC token endpoints from within a
GitHub Actions step. The composition root (`gha_toolkit.runtime`) and the
`gha_toolkit.core` module facade (`core.info(...)`, `core.get_context()`, ...)
are the intended entry points for a user of this package; this module
re-exports the small, curated set of names a user reasonably needs without
digging into submodules, plus `core` itself.
"""

from gha_toolkit import core
from gha_toolkit.commands import AnnotationOptions, ExitCode
from gha_toolkit.context import GitHubContext
from gha_toolkit.exceptions import GhaToolkitError
from gha_toolkit.runtime import ActionsRuntime, create_runtime
from gha_toolkit.summary import ActionSummary

__all__ = [
    'ActionSummary',
    'ActionsRuntime',
    'AnnotationOptions',
    'ExitCode',
    'GhaToolkitError',
    'GitHubContext',
    'core',
    'create_runtime',
]
