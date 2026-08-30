"""`GitHubContext`: a typed dataclass over the runner's context environment variables.

Ported from ``.original/toolkit/packages/github/src/context.ts``'s ``Context``
class. Upstream's field set (``context.ts:11-24``) is: ``eventName``, ``sha``,
``ref``, ``workflow``, ``action``, ``actor``, ``job``, ``runAttempt``,
``runNumber``, ``runId``, ``apiUrl``, ``serverUrl``, ``graphqlUrl``, plus the
``payload`` field this package models separately as
:class:`gha_toolkit.events.WebhookEvent`. This package's field set extends
upstream's with the additional runner variables the fixtures fake
(``tests/fixtures/environment.py``'s ``fake_runner_dotenv_vars``):
``repository``, ``repository_owner``, ``ref_name``, ``ref_type``, ``workspace``
-- upstream's narrower ``Context`` class never modeled these, but the runner
always exports them and callers reasonably expect them on a typed context.
Upstream's ``action`` field (``GITHUB_ACTION``, the *current running action's*
id) is dropped: it is not part of the runner-env surface this port's fixtures
cover, and is out of scope for this ticket.

Field-to-variable mapping is by convention, not per-field annotation: every
field name, upper-cased, is the runner environment variable's name with its
``GITHUB_`` prefix stripped -- e.g. ``event_name`` <-> ``GITHUB_EVENT_NAME``,
``ref_type`` <-> ``GITHUB_REF_TYPE``. :func:`gha_toolkit.binder.get_context`
strips that prefix before delegating to :func:`gha_toolkit.binder.bind`; see
that module's docstring for the full resolution rule, including how
``run_attempt``/``run_number``/``run_id`` are parsed as `int`, how
``api_url``/``server_url``/``graphql_url`` fall back to their documented
defaults when unset, and how the one field with no runner-variable
counterpart -- ``event`` -- is populated separately.

This is an interface-only module: :attr:`GitHubContext.repo` and
:attr:`GitHubContext.issue` raise ``NotImplementedError``. `GitHubContext`,
`ContextRepo`, and `ContextIssue` are pure data and are real, complete
definitions -- direct construction (`GitHubContext(event_name=..., ...)`)
works without raising.
"""

import dataclasses

from gha_toolkit.events import WebhookEvent


@dataclasses.dataclass(frozen=True, slots=True)
class ContextRepo:
    """The `(owner, repo)` pair `GitHubContext.repo` resolves to.

    Parity with upstream `Context.repo`'s return shape (`context.ts:66-82`).
    """

    owner: str
    repo: str


@dataclasses.dataclass(frozen=True, slots=True)
class ContextIssue:
    """The `(owner, repo, number)` triple `GitHubContext.issue` resolves to.

    Parity with upstream `Context.issue`'s return shape (`context.ts:57-64`):
    `owner`/`repo` are `ContextRepo`'s fields, `number` is the triggering
    issue or pull request's number.
    """

    owner: str
    repo: str
    number: int


@dataclasses.dataclass(frozen=True, slots=True)
class GitHubContext:
    """Typed snapshot of the runner's context environment variables.

    See the module docstring for the field-to-variable naming convention and
    for which fields extend upstream's narrower `Context` class. Construction
    is pure data -- every field is a plain value, so
    `GitHubContext(event_name='push', sha='...', ..., event=WebhookEvent(...))`
    works without raising. `repo` and `issue` are the only behavior on this
    class.
    """

    event_name: str
    sha: str
    ref: str
    ref_name: str
    ref_type: str
    repository: str
    repository_owner: str
    workspace: str
    workflow: str
    actor: str
    job: str
    run_attempt: int
    run_number: int
    run_id: int
    event: WebhookEvent
    api_url: str = 'https://api.github.com'
    server_url: str = 'https://github.com'
    graphql_url: str = 'https://api.github.com/graphql'

    @property
    def repo(self) -> ContextRepo:
        """Return the `(owner, repo)` pair this workflow run belongs to.

        Resolution (parity with upstream `Context.repo`, `context.ts:66-82`):
          1. If `self.repository` is non-empty, split it on `'/'` into
             `(owner, repo)`.
          2. Otherwise, if `self.event.payload` has a `repository` key, use
             its `owner.login` and `name`.
          3. Otherwise, raise.

        Raises:
            ValueError: neither source above is available. Message, verbatim
                parity with upstream: "context.repo requires a GITHUB_REPOSITORY environment variable like 'owner/repo'".
                A plain `ValueError` rather than a
                `gha_toolkit.exceptions.GhaToolkitError` subclass is a
                deliberate deviation from this package's typed-exception
                convention: this ticket's file scope does not authorize a
                second additive exception class (see
                `gha_toolkit.exceptions.EventPayloadError`, the one this
                ticket does add), and upstream itself raises a plain,
                untyped `Error` here.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    @property
    def issue(self) -> ContextIssue:
        """Return the `(owner, repo, number)` triple of the triggering issue or PR.

        Resolution (parity with upstream `Context.issue`, `context.ts:57-64`):
        `owner`/`repo` come from `self.repo`; `number` comes from
        `self.event.payload['issue']['number']`, falling back to
        `self.event.payload['pull_request']['number']`, falling back to
        `self.event.payload['number']`.

        Raises:
            ValueError: see `repo`; propagates if `self.repo` raises.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
