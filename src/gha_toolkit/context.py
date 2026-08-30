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
    owner: str
    repo: str


@dataclasses.dataclass(frozen=True, slots=True)
class ContextIssue:
    owner: str
    repo: str
    number: int


@dataclasses.dataclass(frozen=True, slots=True)
class GitHubContext:
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
        raise NotImplementedError

    @property
    def issue(self) -> ContextIssue:
        raise NotImplementedError
