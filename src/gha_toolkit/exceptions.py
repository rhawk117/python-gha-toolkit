"""Typed exception hierarchy for gha_toolkit.

Every exception raised by a public gha_toolkit API is an instance of
:class:`GhaToolkitError` or one of the subclasses defined here, so callers can catch
a single type to handle any toolkit-raised failure. Each subclass corresponds to one
semantic failure mode; catching the specific subclass lets callers distinguish, for
example, a missing required input from a broken runner file handoff.
"""


class GhaToolkitError(Exception):
    """Base class for every exception raised by gha_toolkit.

    Never raised directly; always raised as one of the typed subclasses below.
    Catching this type catches any gha_toolkit-raised failure without also
    swallowing unrelated exceptions raised by other libraries or user code.
    """


class MissingInputError(GhaToolkitError):
    """Raised when a required workflow input has no value.

    Mirrors the upstream `@actions/core` `getInput({ required: true })` contract:
    requesting a required input that is absent, or empty after whitespace trimming,
    raises this instead of silently returning an empty string.
    """


class InputParseError(GhaToolkitError):
    """Raised when converting a workflow input's raw string value fails.

    Typed replacement for upstream `@actions/core`'s bare `TypeError` -- for
    example `getBooleanInput` raising `TypeError('Input does not meet YAML 1.2
    "Core Schema" specification: ...')` when a value is not one of the six
    legal boolean literals. Raised by :meth:`gha_toolkit.inputs.ActionsInputs.get`
    whenever the caller-supplied ``parser`` callable raises on the input's raw
    string value; the stock accessors (:meth:`ActionsInputs.get_boolean` and
    friends) surface this for their own parsing failures the same way, since
    they are implemented on top of :meth:`ActionsInputs.get`.
    """


class MissingRunnerFileError(GhaToolkitError):
    """Raised when a runner-provided command-file environment variable is unset.

    File-based workflow commands (environment variables such as ``GITHUB_ENV``,
    ``GITHUB_OUTPUT``, ``GITHUB_PATH``, ``GITHUB_STATE``, and
    ``GITHUB_STEP_SUMMARY``) depend on the runner exporting a path to a writable
    temp file. This is raised when the corresponding environment variable is
    missing or empty, so the caller learns immediately instead of attempting to
    write to a nonexistent path.
    """


class DelimiterInjectionError(GhaToolkitError):
    """Raised when a value would corrupt a runner file's delimiter framing.

    File commands write ``name<<EOF\\nvalue\\nEOF`` heredoc-style blocks. A value
    that itself contains the generated delimiter could truncate or corrupt the
    written command. This is raised instead of writing an unsafe payload.
    """


class SummaryAccessError(GhaToolkitError):
    """Raised when the job step summary file is accessed but unavailable.

    Writing to the job summary requires the runner to have set
    ``GITHUB_STEP_SUMMARY``. This is raised when a summary operation is attempted
    without that environment variable present.
    """


class OidcFailureError(GhaToolkitError):
    """Raised when requesting an OpenID Connect token from the runner fails.

    Covers both missing ``ACTIONS_ID_TOKEN_REQUEST_URL`` /
    ``ACTIONS_ID_TOKEN_REQUEST_TOKEN`` environment variables and non-success
    responses returned by the OIDC token endpoint itself.
    """


class EventPayloadError(GhaToolkitError):
    """Raised when the triggering webhook event payload cannot be loaded or bound.

    Two raise sites, both in :mod:`gha_toolkit.events`:

    1. :func:`gha_toolkit.events.load_payload` -- reading and parsing the JSON
       payload the triggering webhook wrote to the file named by
       ``GITHUB_EVENT_PATH``. Raised when ``GITHUB_EVENT_PATH`` is unset or
       empty, when the file it names does not exist or cannot be read, or
       when the file's content is not valid JSON.

       Deviation of record: upstream `Context`'s constructor
       (``context.ts:29-40``) never raises for any of these three cases -- a
       missing ``GITHUB_EVENT_PATH`` variable silently leaves ``payload`` as
       ``{}``, and a path that does not exist writes a `GITHUB_EVENT_PATH
       {path} does not exist` note to stdout and *also* leaves ``payload`` as
       ``{}``. This package raises this exception in every one of those
       cases instead of silently defaulting to an empty payload.

    2. :meth:`gha_toolkit.events.WebhookEvent.unwrap` -- binding the loaded
       payload onto a caller-requested event-model dataclass. Raised when the
       payload's event name does not match the requested model's declared
       ``EVENT_NAME``, or when the payload is missing a field the model
       requires.
    """


class InvalidAnnotationError(GhaToolkitError):
    """Raised when annotation options violate a documented invariant.

    Raised when ``start_column`` or ``end_column`` is set while ``start_line`` and
    ``end_line`` differ, or when another invariant documented on
    :class:`gha_toolkit.commands.AnnotationOptions` is violated.
    """
