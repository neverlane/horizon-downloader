#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/download.py" "$@"
fi

echo "Python 3.10+ is required: https://www.python.org/downloads/" >&2
exit 1
