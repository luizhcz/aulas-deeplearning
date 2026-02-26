#!/usr/bin/env bash
set -e
source .venv/bin/activate
uvicorn --app-dir src "$1" --port "${2:-9002}" --reload
