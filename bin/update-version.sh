#!/usr/bin/env sh

# Will update the build.gradle file to match the last Changelog version

cd "$(dirname "$0")/.."
python update_version.py "${@}"