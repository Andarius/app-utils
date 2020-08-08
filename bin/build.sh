#!/bin/bash

set -e

export ANDROID_HOME=$HOME/Library/Android/sdk
readonly BRANCH='master'

readonly ANDROID_PATH=${BUILD_PATH}/android
readonly IOS_PATH=${BUILD_PATH}/ios
readonly _CUR_DIR="$(dirname "$(readlink "$0")")/.."

echo "current dir $_CUR_DIR"
eval "$(pyenv init -)"
pyenv shell 3.8.3
python --version

setup_clean_repo(){
    rm -rf "$1"
    mkdir -p "$1"
    cd "$1"
    git clone "${REPOSITORY_URL}" -b ${BRANCH}
    cd "${PROJECT_NAME}"
    cp /tmp/.env .
    yarn install
}


if [[ "$1" = "android" ]]; then
    echo "Building android"
    setup_clean_repo "${ANDROID_PATH}"
    python "$_CUR_DIR/update_version.py" -p "${PWD}/CHANGELOG.md" --project "${PWD}" --version "${ANDROID_PATH}/version"
    echo "${RELEASE_KEYSTORE}" | base64 -d > android/app/obitrain.keystore
    cd android
    # ./gradlew assembleRelease
    ./gradlew bundleRelease
else
    echo 'Building iOS'
    setup_clean_repo "${IOS_PATH}"
fi
