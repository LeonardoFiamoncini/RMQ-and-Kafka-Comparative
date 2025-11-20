#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOGS_DIR="${ROOT_DIR}/logs"

if [ -d "${LOGS_DIR}" ]; then
    rm -rf "${LOGS_DIR}"
fi

mkdir -p "${LOGS_DIR}"
