"""Workflow-command formatting and escaping, ported from command.test.ts.

Every stub renders a command through `gha_toolkit.sinks.StdoutSink.invoke`
(bound to the `sink` fixture's `WriteRecorder`) rather than calling
`format_command` and comparing strings directly, so the assertions pin the
same observable surface upstream's `assertWriteCalls` checks: what actually
reaches the log stream.
"""

import os
from collections.abc import Callable

import pytest
from tests.fixtures.sink_recorder import WriteRecorder
from tests.markers import pending

from gha_toolkit.commands import ActionCommand, AnnotationOptions
from gha_toolkit.environment import ProcessEnvironment
from gha_toolkit.logger import WorkflowLogger
from gha_toolkit.sinks import StdoutSink


@pytest.mark.parity
@pending
def test_command_only(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'command only'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(ActionCommand(name='some-command', properties={}, message=''))
    sink.assert_writes([f'::some-command::{os.linesep}'])


@pytest.mark.parity
@pending
def test_command_escapes_message(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'command escapes message'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(
            name='some-command',
            properties={},
            message='percent % percent % cr \r cr \r lf \n lf \n',
        )
    )
    sink.assert_writes(
        [
            (
                f'::some-command::percent %25 percent %25 cr %0D cr %0D '
                f'lf %0A lf %0A{os.linesep}'
            )
        ]
    )
    sink.reset()
    stdout_sink.invoke(
        ActionCommand(
            name='some-command', properties={}, message='%25 %25 %0D %0D %0A %0A'
        )
    )
    sink.assert_writes(
        [f'::some-command::%2525 %2525 %250D %250D %250A %250A{os.linesep}']
    )


@pytest.mark.parity
@pending
def test_command_escapes_property(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'command escapes property'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(
            name='some-command',
            properties={
                'name': (
                    'percent % percent % cr \r cr \r lf \n lf \n '
                    'colon : colon : comma , comma ,'
                )
            },
            message='',
        )
    )
    sink.assert_writes(
        [
            (
                f'::some-command name=percent %25 percent %25 cr %0D cr %0D '
                f'lf %0A lf %0A colon %3A colon %3A comma %2C comma %2C::{os.linesep}'
            )
        ]
    )
    sink.reset()
    stdout_sink.invoke(
        ActionCommand(
            name='some-command',
            properties={},
            message='%25 %25 %0D %0D %0A %0A %3A %3A %2C %2C',
        )
    )
    sink.assert_writes(
        [
            (
                f'::some-command::%2525 %2525 %250D %250D %250A %250A '
                f'%253A %253A %252C %252C{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_command_with_message(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'command with message'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(name='some-command', properties={}, message='some message')
    )
    sink.assert_writes([f'::some-command::some message{os.linesep}'])


@pytest.mark.parity
@pending
def test_command_with_message_and_properties(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'command with message and properties'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(
            name='some-command',
            properties={'prop1': 'value 1', 'prop2': 'value 2'},
            message='some message',
        )
    )
    sink.assert_writes(
        [f'::some-command prop1=value 1,prop2=value 2::some message{os.linesep}']
    )


@pytest.mark.parity
@pending
@pytest.mark.parametrize(
    ('properties', 'expected_properties'),
    [
        pytest.param({'prop1': 'value 1'}, 'prop1=value 1', id='one_property'),
        pytest.param(
            {'prop1': 'value 1', 'prop2': 'value 2'},
            'prop1=value 1,prop2=value 2',
            id='two_properties',
        ),
        pytest.param(
            {'prop1': 'value 1', 'prop2': 'value 2', 'prop3': 'value 3'},
            'prop1=value 1,prop2=value 2,prop3=value 3',
            id='three_properties',
        ),
    ],
)
def test_command_renders_property_list_in_insertion_order(
    make_command_sink: Callable[[WriteRecorder], StdoutSink],
    sink: WriteRecorder,
    properties: dict[str, str],
    expected_properties: str,
) -> None:
    """upstream: command.test.ts: 'command with one property'
    upstream: command.test.ts: 'command with two properties'
    upstream: command.test.ts: 'command with three properties'
    """
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(name='some-command', properties=properties, message='')
    )
    sink.assert_writes([f'::some-command {expected_properties}::{os.linesep}'])


@pytest.mark.parity
@pending
def test_command_handles_non_string_objects(
    make_command_sink: Callable[[WriteRecorder], StdoutSink], sink: WriteRecorder
) -> None:
    """upstream: command.test.ts: 'should handle issuing commands for non-string objects'"""
    stdout_sink = make_command_sink(sink)
    stdout_sink.invoke(
        ActionCommand(
            name='some-command',
            properties={'prop1': {'test': 'object'}, 'prop2': 123, 'prop3': True},
            message={'test': 'object'},
        )
    )
    sink.assert_writes(
        [
            (
                f'::some-command prop1={{"test"%3A"object"}},prop2=123,prop3=true'
                f'::{{"test":"object"}}{os.linesep}'
            )
        ]
    )


@pytest.mark.parity
@pending
def test_annotations_map_field_names_correctly(
    make_logger: Callable[[WriteRecorder, ProcessEnvironment], WorkflowLogger],
    sink: WriteRecorder,
    empty_environment: ProcessEnvironment,
) -> None:
    """upstream: core.test.ts: 'annotations map field names correctly'

    Ported against the public logger surface rather than the private
    `_annotation_properties` helper: constructing `AnnotationOptions` and
    routing it through `ActionsLogger.error` exercises the same
    title/file/line/endLine/col/endColumn mapping upstream's
    `toCommandProperties` test asserts directly against a private helper we
    do not expose.
    """
    logger = make_logger(sink, empty_environment)
    options = AnnotationOptions(
        title='A title',
        file='root/test.txt',
        start_line=5,
        end_line=5,
        start_column=1,
        end_column=2,
    )
    logger.error('Error: this is my error message', options=options)
    sink.assert_writes(
        [
            (
                f'::error title=A title,file=root/test.txt,line=5,endLine=5,'
                f'col=1,endColumn=2::Error: this is my error message{os.linesep}'
            )
        ]
    )
