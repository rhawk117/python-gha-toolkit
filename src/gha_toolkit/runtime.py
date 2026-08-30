"""The composition root: ActionsRuntime, create_runtime(), and the current-runtime seam.

Every other module in this package defines an isolated seam or service --
`ActionsInputs`, `ActionsLogger`, `ActionsOutput`/`ActionsState`/`ActionsPaths`,
`ActionsFiles`, `GithubEnvironment`, `ActionStepSummary`, `OidcClient` -- each
a protocol with a minimal concrete stub, constructor-injectable and
independently testable. This module is where they get wired together into
one object a step actually uses: :class:`ActionsRuntime` holds the nine
composed services as public attributes, each annotated against its protocol
rather than a concrete stub; :func:`create_runtime` is the one place that
knows how to build a real, environment-backed instance of it, with
injectable overrides for the seams that need one for tests (`environ`,
`sink`, `delimiter_factory`, `token_transport`); and the module-level
`contextvars.ContextVar` seam -- :func:`current_runtime` / :func:`use_runtime`
-- is how `gha_toolkit.core`'s module-level facade functions find "the"
runtime to delegate to, without a global mutable singleton or a monkeypatched
process environment.

Deliberately no classmethods anywhere in this module: :func:`create_runtime`
is a plain module-level factory function, not `ActionsRuntime.create(...)` /
`ActionsRuntime.from_environment(...)`, so construction is visibly separate
from the `ActionsRuntime` class itself.

This is an interface-only module: :func:`create_runtime`, :func:`current_runtime`,
and :func:`use_runtime` raise ``NotImplementedError``. :class:`ActionsRuntime`
is a plain dataclass composing nine already-constructed services -- composing
one never itself raises; only building those services from scratch
(`create_runtime`) and reading/writing the ContextVar seam
(`current_runtime` / `use_runtime`) do.
"""

import contextlib
import contextvars
import dataclasses
from collections.abc import Callable, MutableMapping

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import ActionsFiles
from gha_toolkit.inputs import ActionsInputs
from gha_toolkit.logger import ActionsLogger
from gha_toolkit.oidc import OidcClient, TokenTransport
from gha_toolkit.services import ActionsOutput, ActionsPaths, ActionsState
from gha_toolkit.sinks import CommandSink
from gha_toolkit.summary import ActionStepSummary


@dataclasses.dataclass(kw_only=True, slots=True)
class ActionsRuntime:
    inputs: ActionsInputs
    logger: ActionsLogger
    output: ActionsOutput
    state: ActionsState
    paths: ActionsPaths
    files: ActionsFiles
    environment: GithubEnvironment
    step_summary: ActionStepSummary
    oidc: OidcClient


def create_runtime(
    *,
    environ: MutableMapping[str, str] | None = None,
    sink: CommandSink | None = None,
    delimiter_factory: Callable[[], str] | None = None,
    token_transport: TokenTransport | None = None,
) -> ActionsRuntime:
    raise NotImplementedError


_current_runtime: contextvars.ContextVar[ActionsRuntime | None] = (
    contextvars.ContextVar('_current_runtime', default=None)
)


def current_runtime() -> ActionsRuntime:
    raise NotImplementedError


def use_runtime(
    runtime: ActionsRuntime,
) -> contextlib.AbstractContextManager[ActionsRuntime]:
    raise NotImplementedError
