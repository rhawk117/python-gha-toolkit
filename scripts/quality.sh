#!/usr/bin/env bash

readonly ERROR_LINE_LIMIT=12

REPOSITORY_ROOT=''
SCRIPTS_DIRECTORY=''
QUALITY_TEMP_DIRECTORY=''

RUN_FORMAT=false
RUN_CHECK=false

declare -A QUALITY_STATUS=()
declare -A QUALITY_ERRORS=()

readonly -a QUALITY_NAMES=(
  python
  shellscript
  markdown
)

readonly -a QUALITY_FUNCTIONS=(
  quality::python
  quality::shellscript
  quality::markdown
)

quality::run_tool() {
  uv run --frozen --group check "$@"
}

quality::collect_shell_files() {
  local -n destination=$1

  # shellcheck disable=SC2034
  mapfile -d '' -t destination < <(
    find "${SCRIPTS_DIRECTORY}" \
      -type f \
      -name '*.sh' \
      -print0 || true
  )
}

quality::abridge_error() {
  local stderr_file=$1

  if [[ ! -s ${stderr_file} ]]; then
    printf '%s\n' 'command failed without stderr'
    return 0
  fi

  tail -n "${ERROR_LINE_LIMIT}" "${stderr_file}"
}

quality::store_error() {
  local group=$1
  local label=$2
  local exit_code=$3
  local stderr_file=$4
  local abridged

  abridged="$(quality::abridge_error "${stderr_file}")"

  QUALITY_ERRORS["${group}"]+="$(
    printf '%s\n' \
      "${label} exited with status ${exit_code}" \
      "${abridged}"
  )"$'\n'
}

quality::run() {
  local group=$1
  local label=$2
  shift 2

  local stderr_file
  local exit_code

  stderr_file="${QUALITY_TEMP_DIRECTORY}/${group}-${RANDOM}.stderr"

  log::info "${label}"

  if "$@" 2> "${stderr_file}"; then
    if [[ -s ${stderr_file} ]]; then
      command cat "${stderr_file}" >&2
    fi

    return 0
  fi

  exit_code=$?
  command cat "${stderr_file}" >&2

  quality::store_error \
    "${group}" \
    "${label}" \
    "${exit_code}" \
    "${stderr_file}"

  return "${exit_code}"
}

quality::python() {
  local phase=$1
  local status=0

  case "${phase}" in
    format)
      quality::run \
        python \
        '[ruff] Apply fixes' \
        quality::run_tool ruff check --fix --unsafe-fixes . ||
        status=1

      quality::run \
        python \
        '[ruff] Format' \
        quality::run_tool ruff format . ||
        status=1
      ;;

    check)
      quality::run \
        python \
        '[ruff] Check formatting' \
        quality::run_tool ruff format --check . ||
        status=1

      quality::run \
        python \
        '[ruff] Lint' \
        quality::run_tool ruff check . ||
        status=1

      quality::run \
        python \
        '[ty] Type check' \
        quality::run_tool ty check --config-file ty.toml ||
        status=1
      ;;

    *)
      log::error "unknown Python quality phase: ${phase}"
      return 2
      ;;
  esac

  return "${status}"
}

quality::shellscript() {
  local phase=$1
  local -a shell_files
  local status=0

  quality::collect_shell_files shell_files

  if ((${#shell_files[@]} == 0)); then
    log::warn '[shellscript] No shell files found'
    return 0
  fi

  case "${phase}" in
    format)
      quality::run \
        shellscript \
        '[shfmt] Format' \
        quality::run_tool shfmt \
        -w \
        -i 2 \
        -ci \
        -sr \
        "${shell_files[@]}" ||
        status=1
      ;;

    check)
      quality::run \
        shellscript \
        '[shfmt] Check formatting' \
        quality::run_tool shfmt \
        -d \
        -i 2 \
        -ci \
        -sr \
        "${shell_files[@]}" ||
        status=1

      quality::run \
        shellscript \
        '[shellcheck] Lint' \
        quality::run_tool shellcheck \
        --external-sources \
        --enable=all \
        "${shell_files[@]}" ||
        status=1
      ;;

    *)
      log::error "unknown shell quality phase: ${phase}"
      return 2
      ;;
  esac

  return "${status}"
}

quality::markdown() {
  local phase=$1
  local status=0

  case "${phase}" in
    format)
      quality::run \
        markdown \
        '[mdformat] Format' \
        quality::run_tool mdformat . ||
        status=1
      ;;

    check)
      quality::run \
        markdown \
        '[mdformat] Check formatting' \
        quality::run_tool mdformat --check . ||
        status=1
      ;;

    *)
      log::error "unknown Markdown quality phase: ${phase}"
      return 2
      ;;
  esac

  return "${status}"
}

quality::run_phase() {
  local phase=$1
  local index
  local name
  local function

  log::step "[Quality] ${phase^} phase"

  for index in "${!QUALITY_FUNCTIONS[@]}"; do
    name=${QUALITY_NAMES[${index}]}
    function=${QUALITY_FUNCTIONS[${index}]}

    log::step "[Quality] ${name}"

    if ! "${function}" "${phase}"; then
      QUALITY_STATUS["${name}"]=1
    fi

    log::step_end
  done

  log::step_end
}

quality::has_failures() {
  local name

  for name in "${QUALITY_NAMES[@]}"; do
    if ((QUALITY_STATUS["${name}"] != 0)); then
      return 0
    fi
  done

  return 1
}

quality::report_failures() {
  local name

  for name in "${QUALITY_NAMES[@]}"; do
    if ((QUALITY_STATUS["${name}"] == 0)); then
      continue
    fi

    log::error "[Quality] ${name} failed"

    if [[ -n ${QUALITY_ERRORS["${name}"]} ]]; then
      printf '%s\n' "${QUALITY_ERRORS["${name}"]}" >&2
    fi
  done
}

quality::initialize_status() {
  local name

  for name in "${QUALITY_NAMES[@]}"; do
    QUALITY_STATUS["${name}"]=0
    QUALITY_ERRORS["${name}"]=''
  done
}

arguments::usage() {
  cat >&2 << EOF
usage: $(basename "$0") [--format] [--check]

Options:
  --format  Apply formatting and safe repository rewrites.
  --check   Run read-only formatting, lint, and type checks.
  -h        Show this help.

When neither phase is specified, both run in this order:
  1. --format
  2. --check
EOF
}

arguments::parse() {
  while (($# > 0)); do
    case "$1" in
      --format)
        RUN_FORMAT=true
        ;;
      --check)
        RUN_CHECK=true
        ;;
      -h | --help)
        arguments::usage
        exit 0
        ;;
      *)
        printf 'unknown argument: %s\n\n' "$1" >&2
        arguments::usage
        return 2
        ;;
    esac

    shift
  done

  if [[ ${RUN_FORMAT} == false && ${RUN_CHECK} == false ]]; then
    RUN_FORMAT=true
    RUN_CHECK=true
  fi
}

environment::initialize() {
  REPOSITORY_ROOT="$(git rev-parse --show-toplevel)"
  SCRIPTS_DIRECTORY="${REPOSITORY_ROOT}/scripts"
  QUALITY_TEMP_DIRECTORY="$(mktemp -d)"

  # shellcheck disable=SC1091
  source "${SCRIPTS_DIRECTORY}/logger.sh"

  cd -- "${REPOSITORY_ROOT}" || exit

  quality::initialize_status
}

environment::cleanup() {
  if [[ -n ${QUALITY_TEMP_DIRECTORY} ]]; then
    rm -rf -- "${QUALITY_TEMP_DIRECTORY}"
  fi
}

main() {
  arguments::parse "$@"
  environment::initialize

  trap environment::cleanup EXIT

  log::info '[uv] Synchronize project and check dependencies'
  uv sync --locked --group check

  [[ ${RUN_FORMAT} == true ]] && quality::run_phase format

  [[ ${RUN_CHECK} == true ]] && quality::run_phase check

  if quality::has_failures; then
    quality::report_failures
    return 1
  fi

  log::success '[Quality] All requested operations passed'
}

main "$@"
