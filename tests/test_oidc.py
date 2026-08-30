"""`OidcClient.get_id_token` contract, ported as extension cases rather than
upstream ports.

Upstream `oidc-utils.test.ts`'s `oidc-client-tests` describe block ('Get Http
Client', 'HTTP get request to get token endpoint') exercises the retrying
`@actions/http-client` instance upstream's `OidcClient` builds internally.
This port's `OidcClient` takes its `TokenTransport` as a constructor argument
instead (see `gha_toolkit.oidc` module docstring), so there is no equivalent
"build an HTTP client" seam left to test -- those two upstream cases are not
cleanly mappable and are intentionally not ported. In their place, this file
exercises the documented `get_id_token` contract (`gha_toolkit/oidc.py`
module docstring, steps 1-6) directly against the fake `FakeTokenTransport`.
"""

import asyncio
from collections.abc import Callable, Mapping
from urllib.parse import quote

import pytest
from tests.fixtures import MakeEnvironment
from tests.fixtures.oidc import FakeTokenTransport
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.exceptions import OidcFailureError
from gha_toolkit.logger import ActionsLogger, WorkflowLogger
from gha_toolkit.oidc import HttpOidcClient


@pytest.fixture
def make_client(
    make_logger: Callable[[WriteRecorder, ProcessEnvironment], WorkflowLogger],
    make_oidc_client: Callable[
        [FakeTokenTransport, ProcessEnvironment, ActionsLogger], HttpOidcClient
    ],
    sink: WriteRecorder,
) -> Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient]:
    """Build an `HttpOidcClient` bound to a fresh `WorkflowLogger`, mirroring
    upstream's `oidc-client-tests` setup, which never asserts against logger
    output -- only `test_security.py`'s masking case does.
    """

    def _make(
        environment: ProcessEnvironment, transport: FakeTokenTransport
    ) -> HttpOidcClient:
        logger = make_logger(sink, environment)
        return make_oidc_client(transport, environment, logger)

    return _make


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_request_token_is_missing(
    make_environment: MakeEnvironment,
    test_token_transport: FakeTokenTransport,
    make_client: Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient],
) -> None:
    """Documented contract, step 1: a missing/empty `ACTIONS_ID_TOKEN_REQUEST_TOKEN`
    raises `OidcFailureError` before any request is issued.
    """
    environment = make_environment({'ACTIONS_ID_TOKEN_REQUEST_TOKEN': ''})
    client = make_client(environment, test_token_transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_request_url_is_missing(
    make_oidc_environment: MakeEnvironment,
    test_token_transport: FakeTokenTransport,
    make_client: Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient],
) -> None:
    """Documented contract, step 2: a missing/empty `ACTIONS_ID_TOKEN_REQUEST_URL`
    raises `OidcFailureError` before any request is issued.
    """
    environment = make_oidc_environment({'ACTIONS_ID_TOKEN_REQUEST_URL': ''})
    client = make_client(environment, test_token_transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())


@pytest.mark.extension
@pending
def test_get_id_token_appends_url_encoded_audience(
    test_oidc_environ: Mapping[str, str],
    make_oidc_environment: MakeEnvironment,
    test_token_transport: FakeTokenTransport,
    make_client: Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient],
) -> None:
    """Documented contract, step 3: a non-`None` audience is URL-encoded and
    appended to the resolved request URL as a literal `&audience=...` suffix.
    """
    environment = make_oidc_environment()
    client = make_client(environment, test_token_transport)
    returned = asyncio.run(client.get_id_token('api://Default & special'))
    assert returned == 'id-token-value'
    expected_url = (
        f'{test_oidc_environ["ACTIONS_ID_TOKEN_REQUEST_URL"]}'
        f'&audience={quote("api://Default & special")}'
    )
    assert test_token_transport.last.url == expected_url
    assert (
        test_token_transport.last.bearer
        == test_oidc_environ['ACTIONS_ID_TOKEN_REQUEST_TOKEN']
    )


@pytest.mark.extension
@pending
def test_get_id_token_wraps_transport_failure(
    make_oidc_environment: MakeEnvironment,
    test_token_transport: FakeTokenTransport,
    make_client: Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient],
) -> None:
    """Documented contract, step 5: an exception raised by the bound transport
    is caught and re-raised as `OidcFailureError`, chained from the original.
    """
    environment = make_oidc_environment()
    transport = test_token_transport.failing(RuntimeError('connection refused'))
    client = make_client(environment, transport)
    with pytest.raises(OidcFailureError) as excinfo:
        asyncio.run(client.get_id_token())
    assert isinstance(excinfo.value.__cause__, RuntimeError)


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_value_field_is_missing(
    make_oidc_environment: MakeEnvironment,
    test_token_transport: FakeTokenTransport,
    make_client: Callable[[ProcessEnvironment, FakeTokenTransport], HttpOidcClient],
) -> None:
    """Documented contract, step 6: a response body that is valid JSON but has
    no (or an empty) `'value'` field raises `OidcFailureError`.
    """
    environment = make_oidc_environment()
    transport = test_token_transport.returning({'notvalue': 'something'})
    client = make_client(environment, transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())
