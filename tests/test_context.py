"""The binder/context deviation layer: `bind`, `get_context`, `get_inputs`,
and `GitHubContext.repo`/`.issue`.

Not upstream ports -- `.original/toolkit/packages/github/src/context.ts`'s
`Context` class is the closest reference material, but this package's
binder-driven design (`bind`, `EnvVar`, `Input`) has no equivalent there, so
every case here is this package's own contract rather than a byte-identical
port. `.repo`/`.issue` follow `Context.repo`/`.issue`'s resolution shape
(`GITHUB_REPOSITORY` split; `payload.issue` falling back to
`payload.pull_request`), adapted to this package's typed `repository` field
and `WebhookEvent.payload`.
"""

import dataclasses
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Annotated

import pytest
from tests.markers import pending

from gha_toolkit.binder import EnvVar, Input, bind, get_context, get_inputs
from gha_toolkit.context import ContextIssue, ContextRepo, GitHubContext
from gha_toolkit.events import JsonValue, WebhookEvent
from gha_toolkit.exceptions import MissingInputError


@dataclasses.dataclass(frozen=True, slots=True)
class TwoFieldRecord:
    name: Annotated[str, EnvVar(name='RECORD_NAME')]
    role: Annotated[str, EnvVar(name='RECORD_ROLE', default='guest')]


@dataclasses.dataclass(frozen=True, slots=True)
class WidgetInputs:
    label: Annotated[str, Input(name='LABEL')]
    count: Annotated[int, Input(name='COUNT', parser=int, required=True)]


@pytest.fixture
def make_context() -> Callable[..., GitHubContext]:
    """A `GitHubContext` with every required field pre-filled to a sensible
    default, so a case only has to override `repository`/`payload`.
    """

    def _make(
        repository: str = 'octocat/hello-world',
        payload: Mapping[str, JsonValue] | None = None,
    ) -> GitHubContext:
        return GitHubContext(
            event_name='push',
            sha='ffac537e6cbbf934b08745a378932722df287a53',
            ref='refs/heads/main',
            ref_name='main',
            ref_type='branch',
            repository=repository,
            repository_owner='octocat',
            workspace='/home/runner/work/hello-world/hello-world',
            workflow='CI',
            actor='octocat',
            job='build',
            run_attempt=1,
            run_number=3,
            run_id=1658821493,
            event=WebhookEvent(event_name='push', payload=payload or {}),
        )

    return _make


@pytest.mark.extension
@pending
def test_bind_populates_fields_from_env_var_metadata() -> None:
    """`bind` resolves each field's source key from its `EnvVar.name`
    metadata and copies the matching mapping value onto the dataclass field
    of the same name.
    """
    record = bind(TwoFieldRecord, {'RECORD_NAME': 'octocat', 'RECORD_ROLE': 'admin'})
    assert record == TwoFieldRecord(name='octocat', role='admin')


@pytest.mark.extension
@pending
def test_bind_falls_back_to_env_var_default_when_key_is_absent() -> None:
    """A field whose `EnvVar.name` key is absent from the mapping falls back
    to `EnvVar.default` rather than raising.
    """
    record = bind(TwoFieldRecord, {'RECORD_NAME': 'octocat'})
    assert record == TwoFieldRecord(name='octocat', role='guest')


@pytest.mark.extension
@pending
def test_get_context_parses_int_fields_from_runner_env(
    fake_runner_dotenv_vars: Mapping[str, str], tmp_path: Path
) -> None:
    """`get_context` parses `run_attempt`/`run_number`/`run_id` as `int` from
    their string-valued `GITHUB_RUN_*` runner variables.
    """
    event_path = tmp_path / 'event.json'
    event_path.write_text('{}', encoding='utf-8')
    environ = {**fake_runner_dotenv_vars, 'GITHUB_EVENT_PATH': str(event_path)}
    context = get_context(environ)
    assert context.run_attempt == int(fake_runner_dotenv_vars['GITHUB_RUN_ATTEMPT'])
    assert context.run_number == int(fake_runner_dotenv_vars['GITHUB_RUN_NUMBER'])
    assert context.run_id == int(fake_runner_dotenv_vars['GITHUB_RUN_ID'])


@pytest.mark.extension
@pending
def test_get_context_falls_back_to_default_urls_when_unset(
    fake_runner_dotenv_vars: Mapping[str, str], tmp_path: Path
) -> None:
    """`api_url`/`server_url`/`graphql_url` fall back to `GitHubContext`'s
    declared defaults when their runner variables are unset, rather than
    raising.
    """
    event_path = tmp_path / 'event.json'
    event_path.write_text('{}', encoding='utf-8')
    unset = {'GITHUB_API_URL', 'GITHUB_SERVER_URL', 'GITHUB_GRAPHQL_URL'}
    environ = {
        key: value for key, value in fake_runner_dotenv_vars.items() if key not in unset
    }
    environ = {**environ, 'GITHUB_EVENT_PATH': str(event_path)}
    context = get_context(environ)
    assert context.api_url == 'https://api.github.com'
    assert context.server_url == 'https://github.com'
    assert context.graphql_url == 'https://api.github.com/graphql'


@pytest.mark.extension
@pending
def test_get_inputs_binds_dataclass_using_input_metadata() -> None:
    """`get_inputs` resolves each field's `INPUT_*` source key from its
    `Input.name` metadata and applies `Input.parser` to the raw string before
    assigning it.
    """
    inputs = get_inputs(WidgetInputs, {'INPUT_LABEL': 'widget', 'INPUT_COUNT': '3'})
    assert inputs == WidgetInputs(label='widget', count=3)


@pytest.mark.extension
@pending
def test_get_inputs_raises_when_required_input_is_missing() -> None:
    """A field marked `Input(required=True)` raises `MissingInputError` when
    its `INPUT_*` key is absent from the mapping.
    """
    with pytest.raises(MissingInputError):
        get_inputs(WidgetInputs, {'INPUT_LABEL': 'widget'})


@pytest.mark.extension
@pending
def test_context_repo_splits_github_repository_into_owner_and_name(
    make_context: Callable[..., GitHubContext],
) -> None:
    """`GitHubContext.repo` splits the `repository` field on its first `/`
    into owner and repo name, ported from upstream `Context.repo`'s
    `GITHUB_REPOSITORY` split.
    """
    context = make_context(repository='octocat/hello-world')
    assert context.repo == ContextRepo(owner='octocat', repo='hello-world')


@pytest.mark.extension
@pending
def test_context_issue_derives_number_from_issue_payload(
    make_context: Callable[..., GitHubContext],
) -> None:
    """`GitHubContext.issue` combines `.repo` with the event payload's
    `issue.number`, ported from upstream `Context.issue`'s
    `(payload.issue || payload.pull_request || payload).number` fallback.
    """
    context = make_context(payload={'issue': {'number': 42}})
    assert context.issue == ContextIssue(owner='octocat', repo='hello-world', number=42)


@pytest.mark.extension
@pending
def test_context_issue_derives_number_from_pull_request_payload_when_no_issue(
    make_context: Callable[..., GitHubContext],
) -> None:
    """When the payload has no `issue` key, `.issue` falls back to
    `pull_request.number`.
    """
    context = make_context(payload={'pull_request': {'number': 7}})
    assert context.issue == ContextIssue(owner='octocat', repo='hello-world', number=7)
