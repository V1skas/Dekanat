#!/bin/sh
set -e

INIT_FLAG="/Dekanat/data/.initialized"
UPDATE_MARKER="/Dekanat/.update_marker"

if [ ! -f "$INIT_FLAG" ]; then
    uv run reflex db migrate
    uv run deploy.py
    touch "$INIT_FLAG"

    if [ -f "$UPDATE_MARKER" ]; then
        rm "$UPDATE_MARKER"
    fi

else
    if [ -f "$UPDATE_MARKER" ]; then
        uv run reflex db migrate
        uv run update.py
        rm "$UPDATE_MARKER"
    fi
fi

# Передаем управление основному процессу (Reflex)
exec "$@"
