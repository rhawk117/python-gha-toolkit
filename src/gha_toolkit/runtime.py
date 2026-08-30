"""The composition root: ActionsRuntime, create_runtime(), and the current-runtime seam.

Every other module in this package defines an isolated seam or service --
`ActionsInputs`, `ActionsLogger`, `ActionsOutput`/`ActionsState`/`ActionsPaths`,
`ActionsFiles`, `GithubEnvironment`, `ActionStepSummary`, `OidcClient` -- each
constructor-injectable and independently testable. This module is where they
get wired together into one object a step actually uses: :class:`ActionsRuntime`
holds the nine composed services as public attributes; :func:`create_runtime`
is the one place that knows how to build a real, environment-backed instance
of it, with injectable overrides for the seams that need one for tests
(`environ`, `sink`, `delimiter_factory`, `token_transport`); and the module-level
`contextvars.ContextVar` seam -- :func:`current_runtime` / :func:`use_runtime`
-- is how `gha_toolkit.core`'s module-level facade functions find "the"
runtime to delegate to, without a global mutable singleton or a monkeypatched
process environment.

Deliberately no classmethods anywhere in this module: :func:`create_runtime`
is a plain module-level factory function, not `ActionsRuntime.create(...)` /
`ActionsRuntime.from_environment(...)`, so construction is visibly separate
from the `ActionsRuntime` class itself.

This is an interface-only module: :func:`create_runtime`, :func:`current_runtime`,
and :func:`use_runtime` raise ``NotImplementedError``. :class:`ActionsRuntime`'s
constructor, which stores its nine arguments, is real -- composing an
`ActionsRuntime` from already-constructed services never itself raises; only
building those services from scratch (`create_runtime`) and reading/writing
the ContextVar seam (`current_runtime` / `use_runtime`) do.
"""

import contextlib
import contextvars
from collections.abc import Callable, MutableMapping

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import ActionsFiles
from gha_toolkit.inputs import ActionsInputs
from gha_toolkit.logger import ActionsLogger
from gha_toolkit.oidc import OidcClient, TokenTransport
from gha_toolkit.services import ActionsOutput, ActionsPaths, ActionsState
from gha_toolkit.sinks import CommandSink
from gha_toolkit.summary import ActionStepSummary


class ActionsRuntime:
    """The composed set of services one GitHub Actions step runs against.

    Nine public attributes, each an already-constructed service from another
    module in this package: :attr:`inputs` (`ActionsInputs`), :attr:`logger`
    (`ActionsLogger`), :attr:`output` (`ActionsOutput`), :attr:`state`
    (`ActionsState`), :attr:`paths` (`ActionsPaths`), :attr:`files`
    (`ActionsFiles`), :attr:`environment` (`GithubEnvironment`),
    :attr:`step_summary` (`ActionStepSummary`), and :attr:`oidc`
    (`OidcClient`). Every `gha_toolkit.core` facade function resolves an
    instance of this class via :func:`current_runtime` and delegates to
    exactly one of these nine attributes' methods.

    This class has no behavior of its own -- no method beyond the
    constructor -- and no classmethod alternate constructors; building a
    real, environment-backed instance is :func:`create_runtime`'s job, not
    this class's.
    """

    inputs: ActionsInputs
    logger: ActionsLogger
    output: ActionsOutput
    state: ActionsState
    paths: ActionsPaths
    files: ActionsFiles
    environment: GithubEnvironment
    step_summary: ActionStepSummary
    oidc: OidcClient

    def __init__(
        self,
        *,
        inputs: ActionsInputs,
        logger: ActionsLogger,
        output: ActionsOutput,
        state: ActionsState,
        paths: ActionsPaths,
        files: ActionsFiles,
        environment: GithubEnvironment,
        step_summary: ActionStepSummary,
        oidc: OidcClient,
    ) -> None:
        """Store the nine already-constructed services as public attributes.

        Every argument is keyword-only and required: this constructor is a
        pure composition step with no defaults of its own and no I/O --
        assembling sensible defaults for each service is `create_runtime`'s
        job, not this class's.
        """
        self.inputs = inputs
        self.logger = logger
        self.output = output
        self.state = state
        self.paths = paths
        self.files = files
        self.environment = environment
        self.step_summary = step_summary
        self.oidc = oidc


def create_runtime(
    *,
    environ: MutableMapping[str, str] | None = None,
    sink: CommandSink | None = None,
    delimiter_factory: Callable[[], str] | None = None,
    token_transport: TokenTransport | None = None,
) -> ActionsRuntime:
    """Build a real, environment-backed :class:`ActionsRuntime`.

    A plain module-level factory function -- not a classmethod -- so that
    every caller constructing a runtime for real use (as opposed to
    `ActionsRuntime`'s constructor, which only composes already-built
    services) goes through this one place. Every keyword parameter is an
    injectable override with a documented default, so tests substitute a
    fake without monkeypatching global process state:

    - `environ`: backs the :class:`gha_toolkit.environment.GithubEnvironment`
      every other composed service reads through. Defaults to `os.environ`.
    - `sink`: the :class:`gha_toolkit.sinks.CommandSink` every workflow
      command `ActionsLogger` issues is written through. Defaults to a
      :class:`gha_toolkit.sinks.StdoutSink` bound to `sys.stdout` under its
      own default :class:`gha_toolkit.sinks.FlushPolicy.PER_COMMAND` policy.
      `ActionsLogger.info`'s unframed stream write always targets
      `sys.stdout` directly, independent of this override -- only the
      command-issuing transport is swapped when `sink` is supplied.
    - `delimiter_factory`: the heredoc-boundary generator every
      `GITHUB_ENV`/`GITHUB_OUTPUT`/`GITHUB_STATE`-bound
      :class:`gha_toolkit.files.KeyValueFile` uses. Defaults to a
      uuid4-based generator, parity with
      `gha_toolkit.files._default_delimiter_factory`. Because that default
      is not itself overridable through
      :meth:`gha_toolkit.files.ActionsFiles.from_environment`, this
      function constructs the five runner files directly (`KeyValueFile`,
      `PathFile`, `StepSummaryFile`) rather than delegating to that
      classmethod, so an injected `delimiter_factory` actually reaches
      `env`/`output`/`state`.
    - `token_transport`: the :class:`gha_toolkit.oidc.TokenTransport` the
      composed :class:`gha_toolkit.oidc.OidcClient` issues its GET through.
      Defaults to the default transport supplied at implementation time (a
      stdlib-backed implementation is not yet part of this package's public
      surface).

    Composition order (for the future implementation): resolve
    `GithubEnvironment(environ)`; construct the five runner files bound to
    it (using `delimiter_factory` for the three `KeyValueFile`s) into an
    `ActionsFiles`; construct `ActionsInputs`, `ActionsLogger` (over `sink`
    and `sys.stdout`), `ActionsOutput`, `ActionsState`, `ActionsPaths`,
    `ActionStepSummary`, and `OidcClient` (over `token_transport` and the
    just-built `ActionsLogger`) from those files and the environment; return
    an `ActionsRuntime` composing all nine. This function does not bind the
    result to the current-runtime seam -- see :func:`use_runtime` for that.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


_current_runtime: contextvars.ContextVar[ActionsRuntime | None] = (
    contextvars.ContextVar('_current_runtime', default=None)
)
"""Private module state backing :func:`current_runtime` / :func:`use_runtime`.

A `contextvars.ContextVar` rather than a plain module-level variable so the
binding is task-local and thread-local, matching the semantics tests need:
concurrently-running coroutines or threads never see each other's bound
runtime. `None` means "no runtime is currently bound". Not part of this
module's public surface -- callers reach it only through
:func:`current_runtime` and :func:`use_runtime`.
"""


def current_runtime() -> ActionsRuntime:
    """Return the `ActionsRuntime` currently bound via :func:`use_runtime`.

    Every `gha_toolkit.core` facade function calls this first, to resolve
    the runtime it delegates to. Reads the private ContextVar seam
    (`_current_runtime`); once implemented, raises
    `gha_toolkit.exceptions.GhaToolkitError` when nothing is bound -- there
    is no implicit default runtime, by design, so that code calling this
    (or a `gha_toolkit.core` function) without first calling `use_runtime`
    or arranging real GitHub Actions process state fails loudly instead of
    silently hitting live `os.environ` / `sys.stdout`.

    Raises:
        NotImplementedError: always; the typed `GhaToolkitError` raised for
            an unbound runtime lands with the rest of this stub's behavior
            in a later task.
    """
    raise NotImplementedError


def use_runtime(
    runtime: ActionsRuntime,
) -> contextlib.AbstractContextManager[ActionsRuntime]:
    """Bind `runtime` as the current runtime for the duration of the returned context.

    `with use_runtime(fake_runtime): ...` is how a test (or a caller
    embedding this package inside a larger process) binds its own
    `ActionsRuntime` -- built by hand, or via `create_runtime` with fakes
    for `environ`/`sink`/`delimiter_factory`/`token_transport` -- for the
    code under test to pick up through `gha_toolkit.core`'s facade
    functions, with no monkeypatching: no `unittest.mock.patch`, and no
    mutation of real `os.environ` or `sys.stdout`. On entry, sets
    `_current_runtime` to
    `runtime`; on exit (including when an exception propagates out of the
    `with` block), restores whatever was bound before entry -- `None` if
    nothing was, or an enclosing `use_runtime`'s runtime if this call is
    nested inside one. The returned context manager's `__enter__` yields
    `runtime` itself, so `with use_runtime(rt) as bound: assert bound is rt`
    holds.

    Raises:
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError
