"""gha_toolkit: a Python port of @actions/core, the GitHub Actions toolkit core package.

This package defines a typed, interface-first surface for writing workflow
commands, reading inputs, managing outputs and state, emitting log annotations,
and interacting with the job summary and OIDC token endpoints from within a
GitHub Actions step. Public re-exports land once the underlying subsystems
(exceptions, wire primitives, transport seams, services, summary, env binder,
platform/OIDC, and the composition root) are implemented; this module is
intentionally minimal until then.
"""
