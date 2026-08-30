import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Self

import pytest

from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.logger import ActionsLogger
from gha_toolkit.oidc import HttpOidcClient


@dataclass(slots=True)
class RecordedRequest:
    url: str
    bearer: str
    timeout: float


@dataclass(slots=True)
class TestTokenTransport:
    body: bytes = b'{"value": "id-token-value"}'
    error: Exception | None = None
    requests: list[RecordedRequest] = field(default_factory=list)

    def get(self, url: str, *, bearer: str, timeout: float) -> bytes:
        self.requests.append(RecordedRequest(url=url, bearer=bearer, timeout=timeout))
        if self.error is not None:
            raise self.error
        return self.body

    @property
    def last(self) -> RecordedRequest:
        return self.requests[-1]

    def returning(self, payload: object) -> Self:
        self.body = json.dumps(payload).encode('utf-8')
        return self

    def failing(self, error: Exception) -> Self:
        self.error = error
        return self


@pytest.fixture
def test_token_transport() -> TestTokenTransport:
    return TestTokenTransport()


@pytest.fixture
def make_oidc_client() -> Callable[
    [TestTokenTransport, GithubEnvironment, ActionsLogger], HttpOidcClient
]:
    def _make(
        transport: TestTokenTransport,
        environment: GithubEnvironment,
        logger: ActionsLogger,
    ) -> HttpOidcClient:
        return HttpOidcClient(transport, environment, logger)

    return _make
