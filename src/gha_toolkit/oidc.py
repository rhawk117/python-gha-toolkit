"""The OpenID Connect token seam: transport shape and the async client built on it.

:class:`TokenTransport` is the structural seam every OIDC HTTP transport
implements: a single synchronous `get(url, *, bearer, timeout) -> bytes`
method. Keeping the transport synchronous while the client
(:class:`OidcClient`) is asynchronous is a deliberate split: the eventual
zero-dependency implementation wraps stdlib `http.client` (a blocking API)
behind this seam, and :class:`OidcClient` runs it off the event loop (for
example via a thread) rather than requiring an async HTTP stack as a
dependency. That wrapping strategy is an implementation detail left to a
later task; this module only fixes the shape both sides agree on.

Ported from ``.original/toolkit/packages/core/src/oidc-utils.ts`` (the whole
file, `OidcClient` class, lines 11-84). Upstream's `OidcClient` is a
collection of static methods backed by a retrying `HttpClient` (`createHttpClient`,
lines 12-26: up to 10 retries). This port makes the equivalent an instance
with its collaborators constructor-injected instead of static state, and
treats retry policy as the transport implementation's concern, not the
client's -- :class:`HttpOidcClient` calls its bound :class:`TokenTransport`
exactly once per :meth:`OidcClient.get_id_token` call and leaves any
retrying to that transport.

:meth:`HttpOidcClient.get_id_token` full contract, steps 1-6 (parity with
`oidc-utils.ts:66-84`):

1. Resolve the bearer credential via
   ``environment.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')``. Missing or empty
   raises :class:`gha_toolkit.exceptions.OidcFailureError` before any
   request is issued.
2. Resolve the request URL via
   ``environment.get('ACTIONS_ID_TOKEN_REQUEST_URL')``. Missing or empty
   raises `OidcFailureError` the same way, before any request is issued.
3. When `audience` is not `None`, URL-encode it and append it to the
   resolved URL as the literal suffix `'&audience={encoded_audience}'` -- an
   `&`, not a `?`, even though the URL has not otherwise been given a query
   string by this method. This is upstream parity, not a bug: the
   runner-provided `ACTIONS_ID_TOKEN_REQUEST_URL` already carries its own
   query string, so appending with `&` is correct for every real request
   even though it looks wrong in isolation.
4. Emit `logger.debug(f'ID token url is {resolved_url}')` before issuing the
   request.
5. Call `transport.get(resolved_url, bearer=bearer, timeout=self.timeout)`.
   An exception raised by the transport is caught and re-raised as
   `OidcFailureError`, chained from the original.
6. Parse the response body as JSON and read its `'value'` field. A response
   that is not valid JSON, or is valid JSON missing `'value'` (or with it
   empty), raises `OidcFailureError`; otherwise `logger.set_secret(token)`
   masks the token in subsequent log output and the token is returned.

Retry policy is deliberately absent from this contract, as above: retrying
(if any) is the bound :class:`TokenTransport` implementation's
responsibility, calling `transport.get` exactly once per invocation.

This is an interface-only module: :meth:`HttpOidcClient.get_id_token` raises
``NotImplementedError``. :class:`TokenTransport` and :class:`OidcClient` are
protocols -- there is no behavior to implement, only shape to satisfy.
"""

import dataclasses
from typing import Protocol, runtime_checkable

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.logger import ActionsLogger


@runtime_checkable
class TokenTransport(Protocol):
    def get(self, url: str, *, bearer: str, timeout: float) -> bytes: ...


@runtime_checkable
class OidcClient(Protocol):
    async def get_id_token(self, audience: str | None = None) -> str: ...


@dataclasses.dataclass(slots=True)
class HttpOidcClient:
    transport: TokenTransport
    environment: GithubEnvironment
    logger: ActionsLogger
    timeout: float = dataclasses.field(default=10.0, kw_only=True)

    async def get_id_token(self, audience: str | None = None) -> str:
        raise NotImplementedError
