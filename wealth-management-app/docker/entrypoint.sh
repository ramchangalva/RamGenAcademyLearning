#!/bin/sh
set -e
# Ensure SQLite directory is writable when mounted as a volume (often root-owned).
if [ -n "${WEALTH_SQLITE_DIR:-}" ]; then
    mkdir -p "$WEALTH_SQLITE_DIR"
    chown -R appuser:appuser "$WEALTH_SQLITE_DIR" 2>/dev/null || true
    chmod 775 "$WEALTH_SQLITE_DIR" 2>/dev/null || true
fi
exec gosu appuser "$@"
