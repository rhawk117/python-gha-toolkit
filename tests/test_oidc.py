"""`OidcClient.get_id_token` contract, ported as extension cases rather than
upstream ports.

Upstream `oidc-utils.test.ts`'s `oidc-client-tests` describe block ('Get Http
Client', 'HTTP get request to get token endpoint') exercises the retrying
`@actions/http-client` instance upstream's `OidcClient` builds internally.
This port's `OidcClient` takes its `TokenTransport` as a constructor argument
instead (see `gha_toolkit.oidc` module docstring), so there is no equivalent
"build an HTTP client" seam left to test -- those two upstream cases are not
cleanly mappable and are intentionally not ported. In their place, this file
exercises the documented `get_id_token` contract (`gha_toolkit/oidc.py`,
`OidcClient.get_id_token` docstring, steps 1-6) directly against the fake
`TestTokenTransport`.
"""

import asyncio
from collections.abc import Mapping
from urllib.parse import quote

import pytest
from tests.fixtures.oidc import TestTokenTransport as OidcTokenTransport
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.exceptions import OidcFailureError
from gha_toolkit.logger import ActionsLogger
from gha_toolkit.oidc import OidcClient
from gha_toolkit.sinks import StdoutSink


def _client(environ: Mapping[str, str], transport: OidcTokenTransport) -> OidcClient:
    environment = GithubEnvironment(dict(environ))
    stream = WriteRecorder()
    logger = ActionsLogger(
        sink=StdoutSink(stream=stream), stream=stream, environment=environment
    )
    return OidcClient(transport, environment, logger)


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_request_token_is_missing(
    test_environ: Mapping[str, str], test_token_transport: OidcTokenTransport
) -> None:
    """Documented contract, step 1: a missing/empty `ACTIONS_ID_TOKEN_REQUEST_TOKEN`
    raises `OidcFailureError` before any request is issued.
    """
    environ = {**test_environ, 'ACTIONS_ID_TOKEN_REQUEST_TOKEN': ''}
    client = _client(environ, test_token_transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_request_url_is_missing(
    test_oidc_environ: Mapping[str, str], test_token_transport: OidcTokenTransport
) -> None:
    """Documented contract, step 2: a missing/empty `ACTIONS_ID_TOKEN_REQUEST_URL`
    raises `OidcFailureError` before any request is issued.
    """
    environ = {**test_oidc_environ, 'ACTIONS_ID_TOKEN_REQUEST_URL': ''}
    client = _client(environ, test_token_transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())


@pytest.mark.extension
@pending
def test_get_id_token_appends_url_encoded_audience(
    test_oidc_environ: Mapping[str, str], test_token_transport: OidcTokenTransport
) -> None:
    """Documented contract, step 3: a non-`None` audience is URL-encoded and
    appended to the resolved request URL as a literal `&audience=...` suffix.
    """
    client = _client(test_oidc_environ, test_token_transport)
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
    test_oidc_environ: Mapping[str, str], test_token_transport: OidcTokenTransport
) -> None:
    """Documented contract, step 5: an exception raised by the bound transport
    is caught and re-raised as `OidcFailureError`, chained from the original.
    """
    transport = test_token_transport.failing(RuntimeError('connection refused'))
    client = _client(test_oidc_environ, transport)
    with pytest.raises(OidcFailureError) as excinfo:
        asyncio.run(client.get_id_token())
    assert isinstance(excinfo.value.__cause__, RuntimeError)


@pytest.mark.extension
@pending
def test_get_id_token_raises_when_value_field_is_missing(
    test_oidc_environ: Mapping[str, str], test_token_transport: OidcTokenTransport
) -> None:
    """Documented contract, step 6: a response body that is valid JSON but has
    no (or an empty) `'value'` field raises `OidcFailureError`.
    """
    transport = test_token_transport.returning({'notvalue': 'something'})
    client = _client(test_oidc_environ, transport)
    with pytest.raises(OidcFailureError):
        asyncio.run(client.get_id_token())
