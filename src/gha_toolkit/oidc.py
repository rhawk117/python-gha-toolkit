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
client's -- :class:`OidcClient` calls its bound :class:`TokenTransport`
exactly once per :meth:`OidcClient.get_id_token` call and leaves any
retrying to that transport.

This is an interface-only module: :meth:`OidcClient.get_id_token` raises
``NotImplementedError``. :class:`TokenTransport` is a protocol -- there is no
behavior to implement, only shape to satisfy -- and stands as a real
definition; :class:`OidcClient`'s constructor, which stores its arguments,
is real.
"""

from typing import Protocol, runtime_checkable

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.logger import ActionsLogger


@runtime_checkable
class TokenTransport(Protocol):
    """The seam every OIDC HTTP transport implements: a single blocking GET.

    A minimal protocol by design -- its sole public member is :meth:`get` --
    so that any object with a matching `get(url, *, bearer, timeout) -> bytes`
    method satisfies it structurally, without needing to inherit from this
    class. Decorated `@runtime_checkable` so callers may `isinstance()`-check
    a candidate transport; `tests/fixtures/oidc.TestTokenTransport` is the
    authoritative example, satisfying this protocol without subclassing it.
    """

    def get(self, url: str, *, bearer: str, timeout: float) -> bytes:
        """Issue a blocking GET to `url` with `bearer` as a Bearer credential.

        Returns the raw response body. What "issue" means -- retry policy,
        connection reuse, TLS configuration -- is entirely up to the
        implementation; this seam only fixes the call shape and the fact
        that a non-2xx response or a transport-level failure is signaled by
        raising, not by a sentinel return value. `timeout` is a per-call
        seconds budget for the whole request.
        """
        ...


class OidcClient:
    """Requests a GitHub Actions OIDC ID token over a bound :class:`TokenTransport`.

    Parity target: upstream `OidcClient.getIDToken` (`oidc-utils.ts:66-84`),
    composed from `getRequestToken` (lines 28-36), `getIDTokenUrl` (lines
    38-44), and `getCall` (lines 46-64). Three collaborators are constructor-
    injected rather than looked up globally the way upstream's static class
    reads `process.env` and imports `debug`/`setSecret` directly:

    - `transport`: the :class:`TokenTransport` that performs the actual GET.
    - `environment`: a `gha_toolkit.environment.GithubEnvironment` read for
      `ACTIONS_ID_TOKEN_REQUEST_TOKEN` and `ACTIONS_ID_TOKEN_REQUEST_URL`.
    - `logger`: a `gha_toolkit.logger.ActionsLogger`, used to `debug` the
      token URL before the request and to `set_secret` the resolved token
      before it is returned.
    """

    def __init__(
        self,
        transport: TokenTransport,
        environment: GithubEnvironment,
        logger: ActionsLogger,
        *,
        timeout: float = 10.0,
    ) -> None:
        """Bind this instance to `transport`, `environment`, `logger`, and `timeout`.

        Storing the four values is the entire constructor; no environment
        variable is read, no log line is written, and no request is issued
        until :meth:`get_id_token` is called. `timeout` is the seconds
        budget passed to every :meth:`TokenTransport.get` call this instance
        makes.
        """
        self._transport = transport
        self._environment = environment
        self._logger = logger
        self._timeout = timeout

    async def get_id_token(self, audience: str | None = None) -> str:
        """Request and return an OIDC ID token, optionally scoped to `audience`.

        Full contract (parity with `oidc-utils.ts:66-84` plus its two
        private helpers):

        1. Resolve the bearer credential via
           `environment.require('ACTIONS_ID_TOKEN_REQUEST_TOKEN')`. Missing
           or empty raises :class:`gha_toolkit.exceptions.OidcFailureError`
           -- typed replacement for upstream's untyped `Error('Unable to get
           ACTIONS_ID_TOKEN_REQUEST_TOKEN env variable')`.
        2. Resolve the request URL via
           `environment.require('ACTIONS_ID_TOKEN_REQUEST_URL')`. Missing or
           empty raises :class:`OidcFailureError` the same way, parity with
           upstream's `Error('Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env
           variable')`.
        3. When `audience` is not `None`, URL-encode it and append it to the
           resolved URL as the literal suffix `'&audience={encoded_audience}'`
           -- an `&`, not a `?`, even though the URL has not otherwise been
           given a query string by this method. This is upstream parity, not
           a bug: the runner-provided `ACTIONS_ID_TOKEN_REQUEST_URL` already
           carries its own query string, so appending with `&` is correct
           for every real request even though it looks wrong in isolation
           (`oidc-utils.ts:70-73`, `encodeURIComponent(audience)`).
        4. Emit `logger.debug(f'ID token url is {resolved_url}')` before
           issuing the request (`oidc-utils.ts:75`).
        5. Call `transport.get(resolved_url, bearer=bearer, timeout=self.
           _timeout)`. A raised exception from the transport is caught and
           re-raised as :class:`OidcFailureError`, chained from the original
           (`raise OidcFailureError(...) from error`) -- typed replacement
           for upstream's `Failed to get ID Token` message built from
           `error.statusCode`/`error.message` (`oidc-utils.ts:52-56`).
        6. Parse the response body as JSON and read its `'value'` field. A
           response that is not valid JSON, or is valid JSON missing
           `'value'` (or with it empty), raises :class:`OidcFailureError` --
           parity with upstream's `Error('Response json body do not have ID
           Token field')` (`oidc-utils.ts:60-61`).
        7. Call `logger.set_secret(token)` so the runner masks the token in
           subsequent log output, then return `token`
           (`oidc-utils.ts:78-79`).

        Retry policy is deliberately absent from this contract: upstream's
        `createHttpClient` retries up to 10 times (`oidc-utils.ts:12-26`);
        in this port, retrying (if any) is the bound :class:`TokenTransport`
        implementation's responsibility, not this client's -- this method
        calls `transport.get` exactly once per invocation.

        Args:
            audience: optional audience string to scope the requested token
                to, URL-encoded and appended per step 3 above. `None` (the
                default) requests an unscoped token.

        Raises:
            gha_toolkit.exceptions.OidcFailureError: for every one of the
                four failure modes enumerated in steps 1, 2, 5, and 6 above.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
