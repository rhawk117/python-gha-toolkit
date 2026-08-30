"""Webhook event payloads: the event-name + raw-JSON wrapper, and hand-written event models.

Ported from ``.original/toolkit/packages/github/src/context.ts``'s payload-loading
logic (``context.ts:29-40``, inside ``Context``'s constructor) and
``interfaces.ts``'s loosely-typed ``WebhookPayload``/``PayloadRepository``
interfaces. This module owns two things:

1. :func:`load_payload`, which reads and parses the JSON file named by
   ``GITHUB_EVENT_PATH``, and :class:`WebhookEvent`, the ``event_name`` +
   parsed-payload pair every :class:`gha_toolkit.context.GitHubContext` carries
   as its ``event`` field. ``WebhookEvent.unwrap`` is the typed-model API this
   package's design targets: ``github_context.event.unwrap(PullRequestEvent)``.

   **Deviation of record**: upstream's ``Context`` constructor never raises for
   a missing or unreadable ``GITHUB_EVENT_PATH`` -- a missing environment
   variable silently leaves ``payload`` as ``{}``, and a path that does not
   exist writes ``GITHUB_EVENT_PATH {path} does not exist`` to stdout and
   *also* leaves ``payload`` as ``{}``. :func:`load_payload` raises
   :class:`gha_toolkit.exceptions.EventPayloadError` in every one of those
   cases -- missing variable, missing/unreadable file, or unparseable JSON --
   instead of silently defaulting to an empty payload.

2. Hand-written dataclasses for the core set of webhook events this package
   ships pre-modeled: :class:`PushEvent`, :class:`PullRequestEvent`,
   :class:`IssuesEvent`, :class:`IssueCommentEvent`, :class:`ReleaseEvent`,
   and :class:`WorkflowDispatchEvent`, plus the shared component models
   (:class:`Repository`, :class:`RepositoryOwner`, :class:`Sender`,
   :class:`IssueRef`, :class:`CommentRef`, :class:`ReleaseRef`) upstream's
   ``interfaces.ts`` types explicitly and every payload embeds. Every event
   model carries a ``raw`` field holding the full untyped payload mapping, so
   fields this hand-written set does not model are never lost -- parity with
   upstream's ``[key: string]: any`` index signatures on every interface in
   ``interfaces.ts``. A generated, exhaustive event-model set is reserved for
   a later task (the ``codegen`` pytest marker registered in ``pytest.toml``
   is reserved for that lane); this hand-written set is the pragmatic core.

This is an interface-only module: :func:`load_payload` and
:meth:`WebhookEvent.unwrap` raise ``NotImplementedError``. Every dataclass here
-- :class:`WebhookEvent` and every event/component model -- is pure data and is
a real, complete definition.
"""

import dataclasses
from collections.abc import Mapping, Sequence
from typing import ClassVar, TypeVar

JsonValue = (
    str | int | float | bool | None | Mapping[str, 'JsonValue'] | Sequence['JsonValue']
)

EventT = TypeVar('EventT')


def load_payload(environ: Mapping[str, str]) -> Mapping[str, JsonValue]:
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class RepositoryOwner:
    login: str
    name: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Repository:
    name: str
    owner: RepositoryOwner
    full_name: str | None = None
    html_url: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Sender:
    type: str
    login: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class IssueRef:
    number: int
    html_url: str | None = None
    body: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class CommentRef:
    id: int
    body: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class ReleaseRef:
    tag_name: str
    name: str | None = None
    body: str | None = None
    draft: bool = False
    prerelease: bool = False
    html_url: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class PushEvent:
    EVENT_NAME: ClassVar[str] = 'push'

    ref: str
    before: str
    after: str
    repository: Repository
    sender: Sender
    forced: bool = False
    created: bool = False
    deleted: bool = False
    compare: str | None = None
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class PullRequestEvent:
    EVENT_NAME: ClassVar[str] = 'pull_request'

    action: str
    number: int
    pull_request: IssueRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class IssuesEvent:
    EVENT_NAME: ClassVar[str] = 'issues'

    action: str
    issue: IssueRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class IssueCommentEvent:
    EVENT_NAME: ClassVar[str] = 'issue_comment'

    action: str
    issue: IssueRef
    comment: CommentRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class ReleaseEvent:
    EVENT_NAME: ClassVar[str] = 'release'

    action: str
    release: ReleaseRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class WorkflowDispatchEvent:
    EVENT_NAME: ClassVar[str] = 'workflow_dispatch'

    ref: str
    repository: Repository
    sender: Sender
    inputs: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class WebhookEvent:
    event_name: str
    payload: Mapping[str, JsonValue]

    def unwrap(self, model_type: type[EventT]) -> EventT:
        raise NotImplementedError
