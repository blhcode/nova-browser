#!/usr/bin/env bash
pkill -f "/linux/nova-browser" 2>/dev/null || true
pkill -f "nova_browser.app" 2>/dev/null || true
sleep 0.2
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NOVA_BROWSER_UI="$ROOT/shared/ui"
export PYTHONPATH="$ROOT/linux:$ROOT/shared/ui:${PYTHONPATH:-}"

# WebKitGTK compositor workarounds for blank WebView on some Linux setups.
export WEBKIT_DISABLE_COMPOSITING_MODE="${WEBKIT_DISABLE_COMPOSITING_MODE:-1}"
export WEBKIT_DISABLE_DMABUF_RENDERER="${WEBKIT_DISABLE_DMABUF_RENDERER:-1}"

# shellcheck source=detect-display.sh
source "$ROOT/scripts/detect-display.sh"

echo "Starting Nova Browser from $ROOT (DISPLAY=${DISPLAY:-unset})" >&2
exec python3 "$ROOT/linux/nova-browser" "$@"
