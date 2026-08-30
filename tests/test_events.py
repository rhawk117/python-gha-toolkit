"""`load_payload`'s `EventPayloadError` cases and `WebhookEvent.unwrap`,
ported as extension cases rather than upstream ports.

`load_payload` diverges from upstream `Context`'s silent `payload = {}`
fallback for a missing or unreadable `GITHUB_EVENT_PATH` -- it raises
`EventPayloadError` in every one of those cases instead (see
`gha_toolkit.events`'s module docstring), so none of these cases carry an
`upstream:` docstring tag.
"""

from pathlib import Path

import pytest
from tests.markers import pending

from gha_toolkit.events import (
    PullRequestEvent,
    PushEvent,
    Repository,
    RepositoryOwner,
    Sender,
    WebhookEvent,
    load_payload,
)
from gha_toolkit.exceptions import EventPayloadError


@pytest.mark.extension
@pending
def test_load_payload_raises_when_event_path_variable_is_missing() -> None:
    """A missing `GITHUB_EVENT_PATH` raises `EventPayloadError` instead of
    silently defaulting to an empty payload.
    """
    with pytest.raises(EventPayloadError):
        load_payload({})


@pytest.mark.extension
@pending
def test_load_payload_raises_when_event_file_does_not_exist(tmp_path: Path) -> None:
    """A `GITHUB_EVENT_PATH` naming a file that does not exist raises
    `EventPayloadError` instead of silently defaulting to an empty payload.
    """
    missing_path = tmp_path / 'missing-event.json'
    with pytest.raises(EventPayloadError):
        load_payload({'GITHUB_EVENT_PATH': str(missing_path)})


@pytest.mark.extension
@pending
def test_load_payload_raises_when_event_path_is_unreadable(tmp_path: Path) -> None:
    """A `GITHUB_EVENT_PATH` that cannot be opened as a file (here, a
    directory) raises `EventPayloadError`.
    """
    unreadable_path = tmp_path / 'event-payload-dir'
    unreadable_path.mkdir()
    with pytest.raises(EventPayloadError):
        load_payload({'GITHUB_EVENT_PATH': str(unreadable_path)})


@pytest.mark.extension
@pending
def test_load_payload_raises_when_event_file_is_not_valid_json(tmp_path: Path) -> None:
    """A `GITHUB_EVENT_PATH` file whose contents do not parse as JSON raises
    `EventPayloadError`.
    """
    bad_json_path = tmp_path / 'bad-event.json'
    bad_json_path.write_text('not json', encoding='utf-8')
    with pytest.raises(EventPayloadError):
        load_payload({'GITHUB_EVENT_PATH': str(bad_json_path)})


@pytest.mark.extension
@pending
def test_unwrap_binds_push_event_payload() -> None:
    """`WebhookEvent.unwrap` binds a push payload's fields onto `PushEvent`."""
    payload = {
        'ref': 'refs/heads/main',
        'before': 'aaaaaaa',
        'after': 'bbbbbbb',
        'repository': {'name': 'hello-world', 'owner': {'login': 'octocat'}},
        'sender': {'type': 'User', 'login': 'octocat'},
    }
    event = WebhookEvent(event_name='push', payload=payload)
    push = event.unwrap(PushEvent)
    assert push == PushEvent(
        ref='refs/heads/main',
        before='aaaaaaa',
        after='bbbbbbb',
        repository=Repository(
            name='hello-world', owner=RepositoryOwner(login='octocat')
        ),
        sender=Sender(type='User', login='octocat'),
        raw=payload,
    )


@pytest.mark.extension
@pending
def test_unwrap_binds_pull_request_event_payload() -> None:
    """`WebhookEvent.unwrap` binds a pull-request payload's fields onto
    `PullRequestEvent`.
    """
    payload = {
        'action': 'opened',
        'number': 1,
        'pull_request': {'number': 1},
        'repository': {'name': 'hello-world', 'owner': {'login': 'octocat'}},
        'sender': {'type': 'User', 'login': 'octocat'},
    }
    event = WebhookEvent(event_name='pull_request', payload=payload)
    pull_request = event.unwrap(PullRequestEvent)
    assert pull_request.action == 'opened'
    assert pull_request.number == 1
    assert pull_request.repository == Repository(
        name='hello-world', owner=RepositoryOwner(login='octocat')
    )
    assert pull_request.sender == Sender(type='User', login='octocat')


@pytest.mark.extension
@pending
def test_unwrap_preserves_raw_payload_including_unmodeled_fields() -> None:
    """`unwrap`'s `raw` field carries the full untyped payload, including
    fields the hand-written model does not declare -- parity with upstream's
    `[key: string]: any` index signatures.
    """
    payload = {
        'ref': 'refs/heads/main',
        'before': 'aaaaaaa',
        'after': 'bbbbbbb',
        'repository': {'name': 'hello-world', 'owner': {'login': 'octocat'}},
        'sender': {'type': 'User', 'login': 'octocat'},
        'unmodeled_field': 'kept',
    }
    event = WebhookEvent(event_name='push', payload=payload)
    push = event.unwrap(PushEvent)
    assert push.raw == payload
