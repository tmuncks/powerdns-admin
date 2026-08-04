#!/bin/sh
set -euo pipefail
cd /app

GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:8080}"

GUNICORN_ARGS="-t ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --bind ${BIND_ADDRESS} --log-level ${GUNICORN_LOGLEVEL}"
if [ "$1" == gunicorn ]; then
    ATTEMPTS=0
    MAX_ATTEMPTS=15
    UPGRADE_LOG="$(mktemp)"
    until /bin/sh -c "flask db upgrade" >"$UPGRADE_LOG" 2>&1; do
        ATTEMPTS=$((ATTEMPTS+1))
        if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
            echo "Database did not become available after $((MAX_ATTEMPTS*2)) seconds, giving up"
            cat "$UPGRADE_LOG" >&2
            rm -f "$UPGRADE_LOG"
            exit 1
        fi
        echo "Database not ready, waiting 2s (attempt $ATTEMPTS/$MAX_ATTEMPTS)"
        sleep 2
    done
    cat "$UPGRADE_LOG"
    rm -f "$UPGRADE_LOG"
    exec "$@" $GUNICORN_ARGS

else
    exec "$@"
fi
