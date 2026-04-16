#!/usr/bin/env bash

# Source this file to add the project root to PYTHONPATH.

# Resolve the directory where this script lives.
_HELPER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"




# Add only the project root and main project directories to PYTHONPATH (exclude envs/)
PROJECT_ROOT="${_HELPER_DIR}"
APP_DIR="${PROJECT_ROOT}/app"
AGENTS_DIR="${APP_DIR}/agents"
API_DIR="${APP_DIR}/api"
MAIN_DIR="${APP_DIR}/main"
TESTS_DIR="${PROJECT_ROOT}/tests"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"

PYTHONPATH_ENTRIES="$PROJECT_ROOT:$APP_DIR:$AGENTS_DIR:$API_DIR:$MAIN_DIR:$TESTS_DIR:$SCRIPTS_DIR"

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="$PYTHONPATH_ENTRIES:${PYTHONPATH}"
else
  export PYTHONPATH="$PYTHONPATH_ENTRIES"
fi

# Set VIRTUAL_ENV and update PATH for the project's virtual environment
VENV_PATH="${_HELPER_DIR}/envs"
if [[ -d "$VENV_PATH" ]]; then
  export VIRTUAL_ENV="$VENV_PATH"
  export PATH="$VENV_PATH/bin:$PATH"
fi

unset _HELPER_DIR
