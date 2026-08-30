"""The workflow-input seam: `INPUT_*` environment variables as typed values.

The runner exposes each `with:` entry of a step as an `INPUT_{NAME}` environment
variable, always a raw string. This module defines the single extension point
every typed accessor is built on: :meth:`ActionsInputs.get`, which takes a
caller-supplied ``parser: Callable[[str], T]`` and applies it to the resolved raw
string. The stock accessors (:meth:`ActionsInputs.get_string`,
:meth:`ActionsInputs.get_boolean`, :meth:`ActionsInputs.get_multiline`) are
convenience wrappers over that same primitive, not a separate code path -- a
caller needing a shape none of them cover (an int, a JSON payload, a custom enum)
reaches for :meth:`ActionsInputs.get` directly with their own parser instead of
this module growing a new accessor per shape.

Ported from ``.original/toolkit/packages/core/src/core.ts``'s `getInput` /
`getMultilineInput` / `getBooleanInput` (core.ts:151-208). Deviation of record:
upstream's `getBooleanInput` raises a bare `TypeError` for a value outside the
YAML 1.2 boolean literal set; every parsing failure in this module -- including
that one, and any failure raised by a caller's own ``parser`` passed to
:meth:`ActionsInputs.get` -- raises the typed
:class:`gha_toolkit.exceptions.InputParseError` instead.

This is an interface-only module: every behavior method below raises
``NotImplementedError``. Only the constructor, which stores its argument, is
real.
"""

from collections.abc import Callable, Sequence
from typing import TypeVar

from gha_toolkit.environment import GithubEnvironment

T = TypeVar('T')
T.__doc__ = """Type parameter for the value :meth:`ActionsInputs.get` returns.

Fixed by whatever ``parser: Callable[[str], T]`` the caller supplies -- `str`
for a passthrough parser, `bool` for a boolean parser, and so on.
"""


class ActionsInputs:
    """Typed access to a step's `with:` inputs, extensible via a parser callable.

    Every accessor on this class -- stock or caller-supplied -- resolves an
    input's raw string the same way: `INPUT_{name.replace(' ', '_').upper()}`
    read from the bound :class:`gha_toolkit.environment.GithubEnvironment`,
    defaulting to `''` when unset. :meth:`get` is the seam every accessor is
    built on; :meth:`get_string`, :meth:`get_boolean`, and
    :meth:`get_multiline` are the stock shapes this package ships, implemented
    as calls into :meth:`get` with a fixed parser rather than as independent
    logic.
    """

    def __init__(self, environment: GithubEnvironment) -> None:
        """Bind this instance to `environment`.

        Storing the reference is the entire constructor; no environment
        variable is read until an accessor is called.
        """
        self._environment = environment

    def get(
        self,
        name: str,
        parser: Callable[[str], T],
        *,
        required: bool = False,
        trim: bool = True,
    ) -> T:
        """Resolve `name`'s raw input string and convert it with `parser`.

        Resolution (parity with upstream `getInput`, core.ts:151-163):
          1. Read `INPUT_{name.replace(' ', '_').upper()}` from the bound
             environment, defaulting to `''` if unset.
          2. If `required` is `True` and that raw value is empty, raise
             `MissingInputError` with message
             `"Input required and not supplied: {name}"` -- checked against
             the raw value, before trimming.
          3. Trim leading/trailing whitespace from the value unless `trim` is
             `False` (upstream's `trimWhitespace` option, inverted and
             defaulted to trim-on, matching upstream's own default of
             trimming unless a caller explicitly opts out).
          4. Call `parser(value)` and return its result.

        Raises:
            gha_toolkit.exceptions.MissingInputError: `required` is `True` and
                the raw value for `name` is empty.
            gha_toolkit.exceptions.InputParseError: `parser(value)` raises any
                exception; that exception is wrapped and re-raised as this
                type. This is the typed replacement for upstream's bare
                `TypeError` (see the module docstring).
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def get_string(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> str:
        """Return `name`'s raw input value as a string.

        Equivalent to `get(name, parser=str, required=required, trim=trim)` --
        a passthrough parser, since the resolved value is already a `str`.

        Raises:
            gha_toolkit.exceptions.MissingInputError: see :meth:`get`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def get_boolean(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> bool:
        """Return `name`'s input value parsed as a YAML 1.2 core-schema boolean.

        Equivalent to calling :meth:`get` with a parser that only accepts the
        six literal strings YAML 1.2's core schema recognizes as boolean
        (parity with upstream `getBooleanInput`, core.ts:198-208):
        `'true'`, `'True'`, `'TRUE'`, `'false'`, `'False'`, `'FALSE'`. Any
        other value -- including other common boolean spellings such as
        `'yes'` or `'1'` -- is a parse failure.

        Raises:
            gha_toolkit.exceptions.MissingInputError: see :meth:`get`.
            gha_toolkit.exceptions.InputParseError: the resolved value is not
                one of the six legal literals above. Upstream raises a bare
                `TypeError` with message `'Input does not meet YAML 1.2 "Core
                Schema" specification: {name}\\nSupport boolean input list:
                \\`true | True | TRUE | false | False | FALSE\\`'` for this
                case; this package raises the typed `InputParseError` instead.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError

    def get_multiline(
        self, name: str, *, required: bool = False, trim: bool = True
    ) -> Sequence[str]:
        """Return `name`'s input value split into a list of non-empty lines.

        Parity with upstream `getMultilineInput` (core.ts:173-186): resolves
        the raw input the same way :meth:`get` does (with `required` applied
        to the raw value, before splitting), splits it on `'\\n'`, drops
        entries that are the empty string, then trims each remaining line
        unless `trim` is `False`.

        Raises:
            gha_toolkit.exceptions.MissingInputError: see :meth:`get`.
            NotImplementedError: always; this is an interface stub.
        """
        raise NotImplementedError
