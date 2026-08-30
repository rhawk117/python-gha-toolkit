import os
from collections.abc import Mapping

import pytest


@pytest.fixture
def fake_toolkit_dotenv_vars() -> Mapping[str, str]:
    return {
        'my var': '',
        'special char var \r\n];': '',
        'my var2': '',
        'my secret': '',
        'special char secret \r\n];': '',
        'my secret2': '',
        'PATH': f'path1{os.pathsep}path2',
        'INPUT_MY_INPUT': 'val',
        'INPUT_MISSING': '',
        'INPUT_SPECIAL_CHARS_\'\t"\\': '\'\t"\\ response ',
        'INPUT_MULTIPLE_SPACES_VARIABLE': 'I have multiple spaces',
        'INPUT_BOOLEAN_INPUT': 'true',
        'INPUT_BOOLEAN_INPUT_TRUE1': 'true',
        'INPUT_BOOLEAN_INPUT_TRUE2': 'True',
        'INPUT_BOOLEAN_INPUT_TRUE3': 'TRUE',
        'INPUT_BOOLEAN_INPUT_FALSE1': 'false',
        'INPUT_BOOLEAN_INPUT_FALSE2': 'False',
        'INPUT_BOOLEAN_INPUT_FALSE3': 'FALSE',
        'INPUT_WRONG_BOOLEAN_INPUT': 'wrong',
        'INPUT_WITH_TRAILING_WHITESPACE': '  some val  ',
        'INPUT_MY_INPUT_LIST': 'val1\nval2\nval3',
        'INPUT_LIST_WITH_TRAILING_WHITESPACE': '  val1  \n  val2  \n  ',
        'STATE_TEST_1': 'state_val',
        'GITHUB_PATH': '',
        'GITHUB_ENV': '',
        'GITHUB_OUTPUT': '',
        'GITHUB_STATE': '',
    }


@pytest.fixture
def fake_runner_dotenv_vars() -> Mapping[str, str]:
    return {
        'GITHUB_REPOSITORY': 'octocat/hello-world',
        'GITHUB_REPOSITORY_ID': '1296269',
        'GITHUB_REPOSITORY_OWNER': 'octocat',
        'GITHUB_WORKSPACE': '/home/runner/work/hello-world/hello-world',
        'GITHUB_EVENT_NAME': 'push',
        'GITHUB_SHA': 'ffac537e6cbbf934b08745a378932722df287a53',
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_REF_NAME': 'main',
        'GITHUB_REF_TYPE': 'branch',
        'GITHUB_RUN_ID': '1658821493',
        'GITHUB_RUN_NUMBER': '3',
        'GITHUB_RUN_ATTEMPT': '1',
        'GITHUB_JOB': 'build',
        'GITHUB_ACTOR': 'octocat',
        'GITHUB_TRIGGERING_ACTOR': 'octocat',
        'GITHUB_API_URL': 'https://api.github.com',
        'GITHUB_GRAPHQL_URL': 'https://api.github.com/graphql',
        'GITHUB_SERVER_URL': 'https://github.com',
        'GITHUB_WORKFLOW': 'CI',
        'GITHUB_WORKFLOW_REF': 'octocat/hello-world/.github/workflows/ci.yml@refs/heads/main',
        'RUNNER_OS': 'Linux',
        'RUNNER_ARCH': 'X64',
        'RUNNER_TEMP': '/home/runner/work/_temp',
        'RUNNER_TOOL_CACHE': '/opt/hostedtoolcache',
    }


@pytest.fixture
def fake_oidc_dotenv_vars() -> Mapping[str, str]:
    return {
        'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://runner.example/token',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request-token-value',
    }


@pytest.fixture
def eol() -> str:
    return os.linesep


@pytest.fixture
def test_environ(
    fake_runner_dotenv_vars: Mapping[str, str],
    fake_toolkit_dotenv_vars: Mapping[str, str],
) -> Mapping[str, str]:
    return {**fake_toolkit_dotenv_vars, **fake_runner_dotenv_vars}


@pytest.fixture
def test_oidc_environ(
    test_environ: Mapping[str, str], fake_oidc_dotenv_vars: Mapping[str, str]
) -> Mapping[str, str]:
    return {**test_environ, **fake_oidc_dotenv_vars}


@pytest.fixture
def fake_os_environ(
    monkeypatch: pytest.MonkeyPatch, test_environ: Mapping[str, str]
) -> Mapping[str, str]:
    for key in list(os.environ):
        monkeypatch.delenv(key, raising=False)

    for key, value in test_environ.items():
        monkeypatch.setenv(key, value)

    return test_environ
