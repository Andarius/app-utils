#!/usr/bin/env sh

cd "$(dirname "$0")/.."
python -m app.android "${@}"