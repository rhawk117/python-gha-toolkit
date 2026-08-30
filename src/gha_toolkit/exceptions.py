"""Typed exception hierarchy for gha_toolkit.

Every exception raised by a public gha_toolkit API is an instance of
:class:`GhaToolkitError` or one of the subclasses defined here, so callers can catch
a single type to handle any toolkit-raised failure. Each subclass corresponds to one
semantic failure mode; catching the specific subclass lets callers distinguish, for
example, a missing required input from a broken runner file handoff.
"""


class GhaToolkitError(Exception):
    pass


class MissingInputError(GhaToolkitError):
    pass


class InputParseError(GhaToolkitError):
    pass


class MissingRunnerFileError(GhaToolkitError):
    pass


class DelimiterInjectionError(GhaToolkitError):
    pass


class SummaryAccessError(GhaToolkitError):
    pass


class OidcFailureError(GhaToolkitError):
    pass


class EventPayloadError(GhaToolkitError):
    pass


class InvalidAnnotationError(GhaToolkitError):
    pass
