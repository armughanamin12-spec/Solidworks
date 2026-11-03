#!/bin/bash
set -euo pipefail

# Cloud sessions only
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

CAD_VERSION="0.10.0"
export PATH="$HOME/.local/bin:$PATH"

# uv is needed to fetch and run cad-server
if ! command -v uvx >/dev/null 2>&1; then
  python3 -m pip install --quiet uv
fi

# Skip the install if this release is already registered and its kernel is built.
# The marker lives in text-to-cad's state folder, so it disappears with the install.
marker="$HOME/.local/state/cad/releases/$CAD_VERSION/.session-start.ok"
if [ ! -f "$marker" ] || ! command -v cad >/dev/null 2>&1 || ! claude plugin list 2>/dev/null | grep -q "text-to-cad@text-to-cad"; then
  rm -f "$marker"
  (cd /tmp && uvx --no-config --managed-python --python 3.14 \
    --from "cad-server==$CAD_VERSION" cad setup --only claude)
  touch "$marker"
fi
