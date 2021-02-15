#!/usr/bin/env sh

# Will print the last version code and version of the app
# ./bin/get-last-version.sh ~/Projects/obiapp/CHANGELOG.md
#


cd "$(dirname "$0")/.." || exit
python -m app.changelog  --last -p "${@}"