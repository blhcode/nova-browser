#!/usr/bin/env bash
# Pick a working X11 display for Nova Browser when DISPLAY is unset.
if [[ -n "${DISPLAY:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi

for candidate in :1 :0 :2; do
  sock="/tmp/.X11-unix/X${candidate#:}"
  if [[ -S "$sock" ]]; then
    export DISPLAY="$candidate"
    return 0 2>/dev/null || exit 0
  fi
done

# Last resort — common default for the first local session.
export DISPLAY=":0"
