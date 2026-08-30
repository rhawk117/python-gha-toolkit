"""Log commands, annotations, groups, secrets, and echo, ported from
core.test.ts. `setFailed` is a `gha_toolkit.core` facade-only concern, so its
three cases go through a hand-assembled `ActionsRuntime` bound via
`use_runtime`; every other case exercises `WorkflowLogger` directly.
"""

import os
from collections.abc import Callable

import pytest
from tests.fixtures import MakeEnvironment
from tests.fixtures.oidc import FakeTokenTransport
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit import core
from gha_toolkit.commands import AnnotationOptions, ExitCode
from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.logger import WorkflowLogger
from gha_toolkit.runtime import ActionsRuntime, use_runtime

MakeLogger = Callable[[WriteRecorder, ProcessEnvironment], WorkflowLogger]
MakeRuntime = Callable[
    [ProcessEnvironment, WriteRecorder, Callable[[], str], FakeTokenTransport],
    ActionsRuntime,
]
LogWithMessage = Callable[[WorkflowLogger, str], None]
LogWithOptions = Callable[[WorkflowLogger, str, AnnotationOptions], None]


@pytest.mark.parity
@pending
def test_set_secret_produces_command(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'setSecret produces the correct command'"""
    logger = make_logger(sink, empty_environment)
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
@pytest.mark.parametrize(
    ('message', 'expected_exit_code', 'expected_write'),
    [
        pytest.param(
            'Failure message',
            ExitCode.FAILURE,
            'Failure message',
            id='plain_message',
        ),
        pytest.param(
            'Failure \r\n\nmessage\r',
            ExitCode.FAILURE,
            'Failure %0D%0A%0Amessage%0D',
            id='escapes_the_message',
        ),
        pytest.param(
            Exception('this is my error message'),
            ExitCode.FAILURE,
            'this is my error message',
            id='handles_error',
        ),
    ],
)
def test_set_failed_sets_exit_code_and_writes_error(
    sink: WriteRecorder,
    make_environment: MakeEnvironment,
    delimiter: Callable[[], str],
    test_token_transport: FakeTokenTransport,
    make_runtime: MakeRuntime,
    message: str | Exception,
    expected_exit_code: ExitCode,
    expected_write: str,
) -> None:
    """upstream: core.test.ts: 'setFailed sets the correct exit code and failure message'
    upstream: core.test.ts: 'setFailed escapes the failure message'
    upstream: core.test.ts: 'setFailed handles Error'
    """
    runtime = make_runtime(make_environment(), sink, delimiter, test_token_transport)
    with use_runtime(runtime):
        exit_code = core.set_failed(message)
    assert exit_code == expected_exit_code
    sink.assert_writes([f'::error::{expected_write}{os.linesep}'])


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('log', 'message', 'expected'),
    [
        pytest.param(
            lambda logger, message: logger.debug(message),
            'Debug',
            'debug::Debug',
            id='debug',
        ),
        pytest.param(
            lambda logger, message: logger.notice(message),
            'Notice',
            'notice::Notice',
            id='notice',
        ),
        pytest.param(
            lambda logger, message: logger.warning(message),
            'Warning',
            'warning::Warning',
            id='warning',
        ),
        pytest.param(
            lambda logger, message: logger.error(message),
            'Error message',
            'error::Error message',
            id='error',
        ),
    ],
)
def test_log_level_sets_the_correct_message(
    make_logger: MakeLogger,
    sink: WriteRecorder,
    empty_environment: ProcessEnvironment,
    log: LogWithMessage,
    message: str,
    expected: str,
) -> None:
    """upstream: core.test.ts: 'debug sets the correct message'
    upstream: core.test.ts: 'notice sets the correct message'
    upstream: core.test.ts: 'warning sets the correct message'
    upstream: core.test.ts: 'error sets the correct error message'
    """
    logger = make_logger(sink, empty_environment)
    log(logger, message)
    sink.assert_writes([f'::{expected}{os.linesep}'])


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('log', 'message', 'expected'),
    [
        pytest.param(
            lambda logger, message: logger.debug(message),
            '\r\ndebug\n',
            'debug::%0D%0Adebug%0A',
            id='debug',
        ),
        pytest.param(
            lambda logger, message: logger.notice(message),
            '\r\nnotice\n',
            'notice::%0D%0Anotice%0A',
            id='notice',
        ),
        pytest.param(
            lambda logger, message: logger.warning(message),
            '\r\nwarning\n',
            'warning::%0D%0Awarning%0A',
            id='warning',
        ),
        pytest.param(
            lambda logger, message: logger.error(message),
            'Error message\r\n\n',
            'error::Error message%0D%0A%0A',
            id='error',
        ),
    ],
)
def test_log_level_escapes_the_message(
    make_logger: MakeLogger,
    sink: WriteRecorder,
    empty_environment: ProcessEnvironment,
    log: LogWithMessage,
    message: str,
    expected: str,
) -> None:
    """upstream: core.test.ts: 'debug escapes the message'
    upstream: core.test.ts: 'notice escapes the message'
    upstream: core.test.ts: 'warning escapes the message'
    upstream: core.test.ts: 'error escapes the error message'
    """
    logger = make_logger(sink, empty_environment)
    log(logger, message)
    sink.assert_writes([f'::{expected}{os.linesep}'])


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('level', 'log'),
    [
        pytest.param(
            'notice', lambda logger, message: logger.notice(message), id='notice'
        ),
        pytest.param(
            'warning', lambda logger, message: logger.warning(message), id='warning'
        ),
        pytest.param(
            'error', lambda logger, message: logger.error(message), id='error'
        ),
    ],
)
def test_annotation_level_handles_an_error_object(
    make_logger: MakeLogger,
    sink: WriteRecorder,
    empty_environment: ProcessEnvironment,
    level: str,
    log: LogWithMessage,
) -> None:
    """upstream: core.test.ts: 'notice handles an error object'
    upstream: core.test.ts: 'warning handles an error object'
    upstream: core.test.ts: 'error handles an error object'
    """
    logger = make_logger(sink, empty_environment)
    log(logger, str(Exception('this is my error message')))
    sink.assert_writes([f'::{level}::this is my error message{os.linesep}'])


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('level', 'log'),
    [
        pytest.param(
            'notice',
            lambda logger, message, options: logger.notice(message, options=options),
            id='notice',
        ),
        pytest.param(
            'warning',
            lambda logger, message, options: logger.warning(message, options=options),
            id='warning',
        ),
        pytest.param(
            'error',
            lambda logger, message, options: logger.error(message, options=options),
            id='error',
        ),
    ],
)
def test_annotation_level_handles_parameters_correctly(
    make_logger: MakeLogger,
    sink: WriteRecorder,
    empty_environment: ProcessEnvironment,
    level: str,
    log: LogWithOptions,
) -> None:
    """upstream: core.test.ts: 'notice handles parameters correctly'
    upstream: core.test.ts: 'warning handles parameters correctly'
    upstream: core.test.ts: 'error handles parameters correctly'
    """
    logger = make_logger(sink, empty_environment)
    options = AnnotationOptions(
        title='A title',
        file='root/test.txt',
        start_column=1,
        end_column=2,
        start_line=5,
        end_line=5,
    )
    log(logger, 'this is my error message', options)
    sink.assert_writes(
        [
            (
                f'::{level} title=A title,file=root/test.txt,line=5,endLine=5,'
                f'col=1,endColumn=2::this is my error message{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_start_group_starts_a_new_group(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'startGroup starts a new group'"""
    logger = make_logger(sink, empty_environment)
    logger.start_group('my-group')
    sink.assert_writes([f'::group::my-group{os.linesep}'])


@pytest.mark.parity
@pending
def test_end_group_ends_new_group(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'endGroup ends new group'"""
    logger = make_logger(sink, empty_environment)
    logger.end_group()
    sink.assert_writes([f'::endgroup::{os.linesep}'])


@pytest.mark.parity
@pending
def test_group_wraps_a_call_in_a_group(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'group wraps an async call in a group'

    Adapted from upstream's async wrapper function to a synchronous context
    manager -- see `gha_toolkit.logger`'s module docstring for why.
    """
    logger = make_logger(sink, empty_environment)
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
def test_is_debug_checks_debug_state(
    make_logger: MakeLogger, make_environment: MakeEnvironment
) -> None:
    """upstream: core.test.ts: 'isDebug check debug state'"""
    logger = make_logger(WriteRecorder(), make_environment())
    assert logger.is_debug() is False
    debug_logger = make_logger(WriteRecorder(), make_environment({'RUNNER_DEBUG': '1'}))
    assert debug_logger.is_debug() is True


@pytest.mark.parity
@pending
def test_set_command_echo_can_enable_echoing(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'setCommandEcho can enable echoing'"""
    logger = make_logger(sink, empty_environment)
    logger.set_command_echo(enabled=True)
    sink.assert_writes([f'::echo::on{os.linesep}'])


@pytest.mark.parity
@pending
def test_set_command_echo_can_disable_echoing(
    make_logger: MakeLogger, sink: WriteRecorder, empty_environment: ProcessEnvironment
) -> None:
    """upstream: core.test.ts: 'setCommandEcho can disable echoing'"""
    logger = make_logger(sink, empty_environment)
    logger.set_command_echo(enabled=False)
    sink.assert_writes([f'::echo::off{os.linesep}'])
