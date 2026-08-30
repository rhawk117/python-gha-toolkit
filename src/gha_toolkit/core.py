"""The `gha_toolkit.core` module facade: `core.info(...)` is the whole user API.

Every function in this module is a thin wrapper: it resolves the current
`gha_toolkit.runtime.ActionsRuntime` via `gha_toolkit.runtime.current_runtime`
(bound by `gha_toolkit.runtime.use_runtime`, or by whatever process wires up
`gha_toolkit.runtime.create_runtime`'s result under real GitHub Actions usage)
and delegates to exactly one of that runtime's nine composed services'
methods. There is no class here for a user to instantiate:
`from gha_toolkit import core; core.info('hello')` / `core.get_context()` /
`core.bind_inputs(MyInputs)` is the complete surface this module offers,
mirroring how upstream `@actions/core` is consumed as a flat module of
functions, not a class.

Parity surface: every function upstream `core.ts` exports at module scope
(`getInput`, `getBooleanInput`, `getMultilineInput`, `setOutput`,
`exportVariable`, `addPath`, `saveState`, `getState`, `setSecret`,
`setCommandEcho`, `setFailed`, `isDebug`, `debug`/`info`/`notice`/`warning`/
`error`, `startGroup`/`endGroup`/`group`) plus this package's own additions
(`get_context`, `bind_inputs`, an async `get_id_token`, and a step-summary
accessor). `get_input` keeps its upstream-parity name; `bind_inputs`, this
package's own dataclass-binding addition, is named for what it does --
binding a whole set of named inputs onto one typed object -- distinct from
`get_input`'s single-value read. `group` is a context manager, not upstream's async wrapper
function -- see `gha_toolkit.logger`'s module docstring for why.

This is an interface-only module: every function below raises
``NotImplementedError``.
"""

import contextlib
from collections.abc import Sequence
from typing import TypeVar

from gha_toolkit.commands import AnnotationOptions, ExitCode, OutputValue
from gha_toolkit.context import GitHubContext
from gha_toolkit.summary import ActionStepSummary

ModelT = TypeVar('ModelT')


def get_input(name: str, *, required: bool = False, trim: bool = True) -> str:
    raise NotImplementedError


def get_boolean_input(name: str, *, required: bool = False, trim: bool = True) -> bool:
    raise NotImplementedError


def get_multiline_input(
    name: str, *, required: bool = False, trim: bool = True
) -> Sequence[str]:
    raise NotImplementedError


def get_context() -> GitHubContext:
    raise NotImplementedError


def bind_inputs(model_type: type[ModelT]) -> ModelT:
    raise NotImplementedError


def set_output(name: str, value: OutputValue) -> None:
    raise NotImplementedError


def export_variable(name: str, value: OutputValue) -> None:
    raise NotImplementedError


def add_path(path: str) -> None:
    raise NotImplementedError


def save_state(name: str, value: OutputValue) -> None:
    raise NotImplementedError


def get_state(name: str) -> str:
    raise NotImplementedError


def set_secret(secret: str) -> None:
    raise NotImplementedError


def set_command_echo(*, enabled: bool) -> None:
    raise NotImplementedError


def set_failed(message: str | Exception) -> ExitCode:
    raise NotImplementedError


def is_debug() -> bool:
    raise NotImplementedError


def debug(message: str) -> None:
    raise NotImplementedError


def info(message: str) -> None:
    raise NotImplementedError


def notice(message: str, options: AnnotationOptions | None = None) -> None:
    raise NotImplementedError


def warning(message: str, options: AnnotationOptions | None = None) -> None:
    raise NotImplementedError


def error(message: str, options: AnnotationOptions | None = None) -> None:
    raise NotImplementedError


def start_group(name: str) -> None:
    raise NotImplementedError


def end_group() -> None:
    raise NotImplementedError


def group(name: str) -> contextlib.AbstractContextManager[None]:
    raise NotImplementedError


async def get_id_token(audience: str | None = None) -> str:
    raise NotImplementedError


def summary() -> ActionStepSummary:
    raise NotImplementedError
