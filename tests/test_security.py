"""The four abuse cases from issue #4, ported as security-marked stubs.

Not upstream ports -- upstream `@actions/toolkit` has no equivalent adversarial
suite, so these cases carry no `upstream:` docstring tag. Each documents the
attack it defends against alongside the assertion:

1. A value crafted to contain the runner-file delimiter must raise
   `DelimiterInjectionError` and leave the target file uncorrupted.
2. Newline / `::` sequences in a logged message must be escaped rather than
   smuggling a second, independently-parsed workflow command into the log.
3. A `set_secret` value must reach the sink only in its escaped form, so its
   own bytes cannot terminate the `::add-mask::` command early.
4. An OIDC ID token must be masked (`set_secret`) before `get_id_token`
   returns it to the caller.

The six delimiter-injection ports in `tests/test_env_files.py`
(`test_export_variable_rejects_delimiter_in_*`, `test_set_output_rejects_delimiter_in_*`,
`test_save_state_rejects_delimiter_in_*`) cover abuse case 1 for `GITHUB_OUTPUT`/
`GITHUB_STATE` and the plain raise-on-injection behavior for `GITHUB_ENV`; the
`GITHUB_ENV` case below additionally asserts the file is left byte-for-byte
uncorrupted, which those ports do not check.
"""

import asyncio
import os
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from tests.fixtures.oidc import TestTokenTransport as OidcTokenTransport
from tests.fixtures.runtime import FROZEN_DELIMITER
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit.environment import GithubEnvironment, ProcessEnvironment
from gha_toolkit.exceptions import DelimiterInjectionError
from gha_toolkit.files import HeredocFile
from gha_toolkit.logger import WorkflowLogger
from gha_toolkit.oidc import HttpOidcClient
from gha_toolkit.sinks import StdoutSink


def _environment_with_file(
    test_environ: Mapping[str, str], env_var: str, file_path: Path
) -> GithubEnvironment:
    file_path.write_text('', encoding='utf-8')
    environ = {**test_environ, env_var: str(file_path)}
    return ProcessEnvironment(dict(environ))


@pytest.mark.security
@pending
def test_delimiter_injection_does_not_corrupt_github_env_file(
    test_environ: Mapping[str, str], tmp_path: Path, delimiter: Callable[[], str]
) -> None:
    """Abuse case 1: a value crafted to contain the exact runner-file
    delimiter, shaped to look like a closed heredoc block followed by a
    smuggled `key=value` pair, must raise `DelimiterInjectionError` and leave
    `GITHUB_ENV` byte-for-byte unchanged rather than writing the corrupted
    block.
    """
    env_path = tmp_path / 'env'
    environment = _environment_with_file(test_environ, 'GITHUB_ENV', env_path)
    env_file = HeredocFile('GITHUB_ENV', environment, delimiter)
    malicious_value = f'harmless{os.linesep}{FROZEN_DELIMITER}{os.linesep}PWNED=1{os.linesep}MYVAR<<{FROZEN_DELIMITER}'
    with pytest.raises(DelimiterInjectionError):
        env_file.set('MYVAR', malicious_value)
    assert env_path.read_text(encoding='utf-8') == ''


@pytest.mark.security
@pending
def test_log_message_escaping_prevents_command_smuggling(sink: WriteRecorder) -> None:
    """Abuse case 2: an attacker-controlled message (for example, reflected
    from a PR title) containing newlines and `::name::` framing must be
    percent-escaped into a single command, not passed through -- an
    unescaped newline would let the message inject a second, independently
    parsed workflow command into the log stream.
    """
    logger = WorkflowLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=ProcessEnvironment({})
    )
    payload = 'legitimate message\n::error::SMUGGLED\n::set-output name=pwned::1'
    logger.notice(payload)
    sink.assert_writes(
        [
            (
                f'::notice::legitimate message%0A::error::SMUGGLED'
                f'%0A::set-output name=pwned::1{os.linesep}'
            )
        ]
    )
    sink.assert_contains_none_of(
        ['\n::error::SMUGGLED', '\n::set-output name=pwned::1']
    )


@pytest.mark.security
@pending
def test_set_secret_value_never_appears_unescaped_in_sink_output(
    sink: WriteRecorder,
) -> None:
    """Abuse case 3: a value handed to `set_secret` must reach the sink only
    in its escaped form -- a value containing a raw `\\r\\n` could otherwise
    let the masked value's own bytes terminate the `::add-mask::` command
    early and inject an unrelated, unmasked line into the log.
    """
    logger = WorkflowLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=ProcessEnvironment({})
    )
    payload = 'super-sensitive\r\nvalue::with::colons'
    logger.set_secret(payload)
    sink.assert_writes(
        [f'::add-mask::super-sensitive%0D%0Avalue::with::colons{os.linesep}']
    )
    sink.assert_contains_none_of([payload])


@pytest.mark.security
@pending
def test_get_id_token_masks_the_token_before_returning(
    test_oidc_environ: Mapping[str, str],
    test_token_transport: OidcTokenTransport,
    sink: WriteRecorder,
) -> None:
    """Abuse case 4: `get_id_token` must call `logger.set_secret` on the
    resolved token before returning it, so the runner masks the token in any
    log output emitted after this call -- an OIDC ID token is exactly the
    kind of high-privilege credential that must never appear unmasked in a
    job log.
    """
    environment = ProcessEnvironment(dict(test_oidc_environ))
    logger = WorkflowLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=environment
    )
    client = HttpOidcClient(test_token_transport, environment, logger)
    returned = asyncio.run(client.get_id_token())
    assert returned == 'id-token-value'
    sink.assert_writes([f'::add-mask::id-token-value{os.linesep}'])
