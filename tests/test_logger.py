"""Log commands, annotations, groups, secrets, and echo, ported from
core.test.ts. `setFailed` is a `gha_toolkit.core` facade-only concern, so its
three cases go through a hand-assembled `ActionsRuntime` bound via
`use_runtime`; every other case exercises `ActionsLogger` directly.
"""

import os
from collections.abc import Callable, Mapping

import pytest
from tests.fixtures.oidc import TestTokenTransport as OidcTokenTransport
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit import core
from gha_toolkit.commands import AnnotationOptions, ExitCode
from gha_toolkit.environment import GithubEnvironment
from gha_toolkit.files import ActionsFiles, KeyValueFile, PathFile, StepSummaryFile
from gha_toolkit.inputs import ActionsInputs
from gha_toolkit.logger import ActionsLogger
from gha_toolkit.oidc import OidcClient
from gha_toolkit.runtime import ActionsRuntime, use_runtime
from gha_toolkit.services import ActionsOutput, ActionsPaths, ActionsState
from gha_toolkit.sinks import StdoutSink
from gha_toolkit.summary import ActionStepSummary


def _build_runtime(
    test_environ: Mapping[str, str],
    sink: WriteRecorder,
    delimiter: Callable[[], str],
    test_token_transport: OidcTokenTransport,
) -> ActionsRuntime:
    """Compose a full `ActionsRuntime` from already-constructed services.

    Every call below is a plain constructor storing its arguments -- none of
    them raise -- so building this runtime never itself triggers the pending
    xfail; only calling a method on one of its services does.
    """
    environment = GithubEnvironment(dict(test_environ))
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=environment
    )
    files = ActionsFiles(
        env=KeyValueFile('GITHUB_ENV', environment, delimiter),
        output=KeyValueFile('GITHUB_OUTPUT', environment, delimiter),
        state=KeyValueFile('GITHUB_STATE', environment, delimiter),
        path=PathFile('GITHUB_PATH', environment),
        step_summary=StepSummaryFile('GITHUB_STEP_SUMMARY', environment),
    )
    return ActionsRuntime(
        inputs=ActionsInputs(environment),
        logger=logger,
        output=ActionsOutput(files.output),
        state=ActionsState(files.state, environment),
        paths=ActionsPaths(files.path, environment),
        files=files,
        environment=environment,
        step_summary=ActionStepSummary(files.step_summary),
        oidc=OidcClient(test_token_transport, environment, logger),
    )


@pytest.mark.parity
@pending
def test_set_secret_produces_command(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'setSecret produces the correct command'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.set_secret('secret val')
    logger.set_secret('multi\nline\r\nsecret')
    sink.assert_writes(
        [
            f'::add-mask::secret val{os.linesep}',
            f'::add-mask::multi%0Aline%0D%0Asecret{os.linesep}',
        ]
    )


@pytest.mark.parity
@pending
def test_set_failed_sets_exit_code_and_message(
    sink: WriteRecorder,
    test_environ: Mapping[str, str],
    delimiter: Callable[[], str],
    test_token_transport: OidcTokenTransport,
) -> None:
    """upstream: core.test.ts: 'setFailed sets the correct exit code and failure message'"""
    runtime = _build_runtime(test_environ, sink, delimiter, test_token_transport)
    with use_runtime(runtime):
        exit_code = core.set_failed('Failure message')
    assert exit_code == ExitCode.FAILURE
    sink.assert_writes([f'::error::Failure message{os.linesep}'])


@pytest.mark.parity
@pending
def test_set_failed_escapes_the_failure_message(
    sink: WriteRecorder,
    test_environ: Mapping[str, str],
    delimiter: Callable[[], str],
    test_token_transport: OidcTokenTransport,
) -> None:
    """upstream: core.test.ts: 'setFailed escapes the failure message'"""
    runtime = _build_runtime(test_environ, sink, delimiter, test_token_transport)
    with use_runtime(runtime):
        exit_code = core.set_failed('Failure \r\n\nmessage\r')
    assert exit_code == ExitCode.FAILURE
    sink.assert_writes([f'::error::Failure %0D%0A%0Amessage%0D{os.linesep}'])


@pytest.mark.parity
@pending
def test_set_failed_handles_error(
    sink: WriteRecorder,
    test_environ: Mapping[str, str],
    delimiter: Callable[[], str],
    test_token_transport: OidcTokenTransport,
) -> None:
    """upstream: core.test.ts: 'setFailed handles Error'"""
    runtime = _build_runtime(test_environ, sink, delimiter, test_token_transport)
    with use_runtime(runtime):
        exit_code = core.set_failed(Exception('this is my error message'))
    assert exit_code == ExitCode.FAILURE
    sink.assert_writes([f'::error::this is my error message{os.linesep}'])


@pytest.mark.parity
@pending
def test_error_sets_the_correct_error_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'error sets the correct error message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.error('Error message')
    sink.assert_writes([f'::error::Error message{os.linesep}'])


@pytest.mark.parity
@pending
def test_error_escapes_the_error_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'error escapes the error message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.error('Error message\r\n\n')
    sink.assert_writes([f'::error::Error message%0D%0A%0A{os.linesep}'])


@pytest.mark.parity
@pending
def test_error_handles_an_error_object(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'error handles an error object'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.error(str(Exception('this is my error message')))
    sink.assert_writes([f'::error::this is my error message{os.linesep}'])


@pytest.mark.parity
@pending
def test_error_handles_parameters_correctly(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'error handles parameters correctly'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    options = AnnotationOptions(
        title='A title',
        file='root/test.txt',
        start_column=1,
        end_column=2,
        start_line=5,
        end_line=5,
    )
    logger.error('this is my error message', options=options)
    sink.assert_writes(
        [
            (
                f'::error title=A title,file=root/test.txt,line=5,endLine=5,'
                f'col=1,endColumn=2::this is my error message{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_warning_sets_the_correct_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'warning sets the correct message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.warning('Warning')
    sink.assert_writes([f'::warning::Warning{os.linesep}'])


@pytest.mark.parity
@pending
def test_warning_escapes_the_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'warning escapes the message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.warning('\r\nwarning\n')
    sink.assert_writes([f'::warning::%0D%0Awarning%0A{os.linesep}'])


@pytest.mark.parity
@pending
def test_warning_handles_an_error_object(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'warning handles an error object'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.warning(str(Exception('this is my error message')))
    sink.assert_writes([f'::warning::this is my error message{os.linesep}'])


@pytest.mark.parity
@pending
def test_warning_handles_parameters_correctly(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'warning handles parameters correctly'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    options = AnnotationOptions(
        title='A title',
        file='root/test.txt',
        start_column=1,
        end_column=2,
        start_line=5,
        end_line=5,
    )
    logger.warning('this is my error message', options=options)
    sink.assert_writes(
        [
            (
                f'::warning title=A title,file=root/test.txt,line=5,endLine=5,'
                f'col=1,endColumn=2::this is my error message{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_notice_sets_the_correct_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'notice sets the correct message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.notice('Notice')
    sink.assert_writes([f'::notice::Notice{os.linesep}'])


@pytest.mark.parity
@pending
def test_notice_escapes_the_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'notice escapes the message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.notice('\r\nnotice\n')
    sink.assert_writes([f'::notice::%0D%0Anotice%0A{os.linesep}'])


@pytest.mark.parity
@pending
def test_notice_handles_an_error_object(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'notice handles an error object'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.notice(str(Exception('this is my error message')))
    sink.assert_writes([f'::notice::this is my error message{os.linesep}'])


@pytest.mark.parity
@pending
def test_notice_handles_parameters_correctly(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'notice handles parameters correctly'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    options = AnnotationOptions(
        title='A title',
        file='root/test.txt',
        start_column=1,
        end_column=2,
        start_line=5,
        end_line=5,
    )
    logger.notice('this is my error message', options=options)
    sink.assert_writes(
        [
            (
                f'::notice title=A title,file=root/test.txt,line=5,endLine=5,'
                f'col=1,endColumn=2::this is my error message{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_start_group_starts_a_new_group(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'startGroup starts a new group'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.start_group('my-group')
    sink.assert_writes([f'::group::my-group{os.linesep}'])


@pytest.mark.parity
@pending
def test_end_group_ends_new_group(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'endGroup ends new group'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.end_group()
    sink.assert_writes([f'::endgroup::{os.linesep}'])


@pytest.mark.parity
@pending
def test_group_wraps_a_call_in_a_group(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'group wraps an async call in a group'

    Adapted from upstream's async wrapper function to a synchronous context
    manager -- see `ActionsLogger.group`'s docstring for why.
    """
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    with logger.group('mygroup'):
        sink.write('in my group\n')
    sink.assert_writes(
        [
            f'::group::mygroup{os.linesep}',
            'in my group\n',
            f'::endgroup::{os.linesep}',
        ]
    )


@pytest.mark.parity
@pending
def test_debug_sets_the_correct_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'debug sets the correct message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.debug('Debug')
    sink.assert_writes([f'::debug::Debug{os.linesep}'])


@pytest.mark.parity
@pending
def test_debug_escapes_the_message(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'debug escapes the message'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.debug('\r\ndebug\n')
    sink.assert_writes([f'::debug::%0D%0Adebug%0A{os.linesep}'])


@pytest.mark.parity
@pending
def test_is_debug_checks_debug_state(test_environ: Mapping[str, str]) -> None:
    """upstream: core.test.ts: 'isDebug check debug state'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=WriteRecorder()),
        stream=WriteRecorder(),
        environment=GithubEnvironment(dict(test_environ)),
    )
    assert logger.is_debug() is False
    debug_environ = {**test_environ, 'RUNNER_DEBUG': '1'}
    debug_logger = ActionsLogger(
        sink=StdoutSink(stream=WriteRecorder()),
        stream=WriteRecorder(),
        environment=GithubEnvironment(dict(debug_environ)),
    )
    assert debug_logger.is_debug() is True


@pytest.mark.parity
@pending
def test_set_command_echo_can_enable_echoing(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'setCommandEcho can enable echoing'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.set_command_echo(enabled=True)
    sink.assert_writes([f'::echo::on{os.linesep}'])


@pytest.mark.parity
@pending
def test_set_command_echo_can_disable_echoing(sink: WriteRecorder) -> None:
    """upstream: core.test.ts: 'setCommandEcho can disable echoing'"""
    logger = ActionsLogger(
        sink=StdoutSink(stream=sink), stream=sink, environment=GithubEnvironment({})
    )
    logger.set_command_echo(enabled=False)
    sink.assert_writes([f'::echo::off{os.linesep}'])
