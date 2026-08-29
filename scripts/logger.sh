#!/usr/bin/env bash

# a thin wrapper around logging to stdout/stderr with color and GitHub Actions support

_COLOR_RED='\033[0;31m'
_COLOR_GREEN='\033[0;32m'
_COLOR_YELLOW='\033[1;33m'
_COLOR_BLUE='\033[0;34m'
_COLOR_CYAN='\033[0;36m'
_COLOR_BOLD='\033[1m'
_COLOR_RESET='\033[0m'

declare -Ar LOG_COLOR=(
  [info]="${_COLOR_BLUE}"
  [success]="${_COLOR_GREEN}"
  [warn]="${_COLOR_YELLOW}"
  [error]="${_COLOR_RED}"
)

declare -Ar LOG_LABEL=(
  [info]="[info]"
  [success]="[ok]"
  [warn]="[warn]"
  [error]="[error]"
)

declare -Ar LOG_ACTION=(
  [info]="info"
  [success]="notice"
  [warn]="warning"
  [error]="error"
)

log::in_github_actions() {
  [[ ${GITHUB_ACTIONS:-false} == "true" ]]
}

log::write() {
  local level=$1
  shift

  if log::in_github_actions; then
    printf '::%s::%s\n' "${LOG_ACTION[${level}]}" "$*"
    return
  fi

  if [[ ${level} == warn || ${level} == error ]]; then
    printf '%b%s%b  %s\n' \
      "${LOG_COLOR[${level}]}" \
      "${LOG_LABEL[${level}]}" \
      "${_COLOR_RESET}" \
      "$*" >&2
  else
    printf '%b%s%b  %s\n' \
      "${LOG_COLOR[${level}]}" \
      "${LOG_LABEL[${level}]}" \
      "${_COLOR_RESET}" \
      "$*"
  fi
}

log::info() { log::write info "$@"; }
log::success() { log::write success "$@"; }
log::warn() { log::write warn "$@"; }
log::error() { log::write error "$@"; }

log::step() {
  if log::in_github_actions; then
    printf '::group::%s\n' "$*"
  else
    printf '\n%b===> %s%b\n' "${_COLOR_BOLD}${_COLOR_CYAN}" "$*" "${_COLOR_RESET}"
  fi
}

log::step_end() {
  log::in_github_actions && printf '%s\n' '::endgroup::'
}

binary::is_installed() {
  command -v "$1" > /dev/null 2>&1
}

binary::required() {
  binary::is_installed "$1" && return

  log::error "Required command not found: $1"
  return 1
}

quality::run_check() {
  local label=$1
  shift

  log::step "${label}"

  if "$@"; then
    log::success "${label}"
    log::step_end
    return 0
  fi

  local status=$?

  log::error "${label}"
  log::step_end

  return "${status}"
}
