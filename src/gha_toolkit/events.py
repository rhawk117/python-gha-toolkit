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
"""The set of shapes a parsed `GITHUB_EVENT_PATH` JSON document can contain.

Structurally identical to `gha_toolkit.commands.OutputValue`, but defined
separately here: that type describes values *serialized* into a workflow
command, while this one describes values *deserialized* from a webhook
payload -- the two happen to share a shape by coincidence of both being
"JSON-compatible Python values", not because one is derived from the other.
"""

EventT = TypeVar('EventT')
EventT.__doc__ = """Type parameter for :meth:`WebhookEvent.unwrap`'s return value.

Fixed by whatever event-model dataclass (`PushEvent`, `PullRequestEvent`, a
caller's own hand-written or generated model, ...) the caller passes as
`model_type`.
"""


def load_payload(environ: Mapping[str, str]) -> Mapping[str, JsonValue]:
    """Read and parse the JSON payload named by `GITHUB_EVENT_PATH` in `environ`.

    Parity target: the payload-loading half of upstream `Context`'s
    constructor (`context.ts:29-40`), minus its silent-`{}`-plus-stdout-note
    fallback -- see the module docstring's "Deviation of record" for the
    three cases (missing variable, missing/unreadable file, invalid JSON)
    this function raises for instead.

    Raises:
        gha_toolkit.exceptions.EventPayloadError: `GITHUB_EVENT_PATH` is
            absent from `environ` or empty; the file it names does not exist
            or cannot be read; or the file's content is not valid JSON.
        NotImplementedError: always; this is an interface stub.
    """
    raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class RepositoryOwner:
    """The `owner` sub-object of a webhook payload's `repository` object.

    Parity with upstream `PayloadRepository.owner` (`interfaces.ts:7-11`):
    `login` is the one field upstream types as required; `name` is
    upstream-optional. Every other key GitHub's actual payload includes on
    this object is not modeled individually here.
    """

    login: str
    name: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Repository:
    """A webhook payload's `repository` object.

    Parity with upstream `PayloadRepository` (`interfaces.ts:3-13`): `name`
    and `owner` are upstream-required; `full_name` and `html_url` are
    upstream-optional. Shared by every event model below via a `repository`
    field, since GitHub embeds this exact shape in nearly every webhook
    payload.
    """

    name: str
    owner: RepositoryOwner
    full_name: str | None = None
    html_url: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Sender:
    """A webhook payload's `sender` object.

    Parity with upstream `WebhookPayload.sender` (`interfaces.ts:30-33`):
    `type` is the one field upstream types explicitly (e.g. `'User'`,
    `'Organization'`, `'Bot'`). `login` is included here as the one other
    field callers commonly need, even though upstream leaves it untyped;
    everything else GitHub's actual payload includes on this object belongs
    in the enclosing event model's `raw` field instead.
    """

    type: str
    login: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class IssueRef:
    """The lightweight `issue`/`pull_request` sub-object shape shared by both.

    Parity with upstream `WebhookPayload.issue`/`.pull_request`
    (`interfaces.ts:18-29`), which type both with this identical shape:
    `number` is upstream-required, `html_url`/`body` are upstream-optional.
    Full issue/pull-request detail is not modeled here -- see the enclosing
    event model's `raw` field.
    """

    number: int
    html_url: str | None = None
    body: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class CommentRef:
    """The `comment` sub-object of an `issue_comment` event payload.

    Parity with upstream `WebhookPayload.comment` (`interfaces.ts:39-42`):
    `id` is the one field upstream types explicitly. `body` is included here
    as the one other field callers commonly need; everything else belongs in
    the enclosing event model's `raw` field.
    """

    id: int
    body: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class ReleaseRef:
    """The `release` sub-object of a `release` event payload.

    Upstream `interfaces.ts` does not type the `release` webhook's payload at
    all (`WebhookPayload` is a generic catch-all); this shape is modeled here
    from GitHub's own webhook documentation for the fields callers most
    commonly need. Everything else belongs in `ReleaseEvent.raw`.
    """

    tag_name: str
    name: str | None = None
    body: str | None = None
    draft: bool = False
    prerelease: bool = False
    html_url: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class PushEvent:
    """The `push` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding.
    """

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
    """The `pull_request` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding.
    """

    EVENT_NAME: ClassVar[str] = 'pull_request'

    action: str
    number: int
    pull_request: IssueRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class IssuesEvent:
    """The `issues` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding.
    """

    EVENT_NAME: ClassVar[str] = 'issues'

    action: str
    issue: IssueRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class IssueCommentEvent:
    """The `issue_comment` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding.
    """

    EVENT_NAME: ClassVar[str] = 'issue_comment'

    action: str
    issue: IssueRef
    comment: CommentRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class ReleaseEvent:
    """The `release` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding.
    """

    EVENT_NAME: ClassVar[str] = 'release'

    action: str
    release: ReleaseRef
    repository: Repository
    sender: Sender
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class WorkflowDispatchEvent:
    """The `workflow_dispatch` webhook event payload.

    Hand-written core-set model (see module docstring). `EVENT_NAME` is the
    canonical GitHub event name :meth:`WebhookEvent.unwrap` matches against
    `WebhookEvent.event_name` before binding. `inputs` holds the workflow's
    caller-defined `workflow_dispatch` input values, which have no fixed
    shape -- unlike step `with:` inputs (`gha_toolkit.inputs.ActionsInputs`),
    these are whatever JSON the dispatch request supplied.
    """

    EVENT_NAME: ClassVar[str] = 'workflow_dispatch'

    ref: str
    repository: Repository
    sender: Sender
    inputs: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)
    raw: Mapping[str, JsonValue] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class WebhookEvent:
    """The webhook payload that triggered this workflow run: event name + raw JSON.

    `gha_toolkit.context.GitHubContext.event` is always an instance of this
    class, built by `gha_toolkit.binder.get_context` from `GITHUB_EVENT_NAME`
    and :func:`load_payload`'s result. Construction itself is pure data --
    only :meth:`unwrap` has behavior.
    """

    event_name: str
    payload: Mapping[str, JsonValue]

    def unwrap(self, model_type: type[EventT]) -> EventT:
        """Bind `payload` onto `model_type`, a hand-written or generated event model.

        Resolution (documented for the future implementation; not yet
        enforced):
          1. If `model_type.EVENT_NAME` (see e.g. `PushEvent.EVENT_NAME`)
             does not equal `self.event_name`, raise
             `gha_toolkit.exceptions.EventPayloadError` -- the loaded payload
             is not an instance of the requested event.
          2. Construct `model_type` from `payload`: known fields (including
             nested component models such as `Repository`/`Sender`) are
             populated from matching payload keys; any top-level payload key
             `model_type` does not model is preserved in the constructed
             instance's `raw` field, unmodified.
          3. If a field `model_type` requires is absent from `payload`, raise
             `gha_toolkit.exceptions.EventPayloadError`.

        Raises:
            gha_toolkit.exceptions.EventPayloadError: `model_type.EVENT_NAME`
                does not match `self.event_name`, or `payload` is missing a
                field `model_type` requires.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
