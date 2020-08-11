#!/usr/bin/env sh

set -e

export ANDROID_HOME="$HOME/Library/Android/sdk"
readonly BRANCH='master'

readonly ANDROID_PATH="${BUILD_PATH}/android"
readonly IOS_PATH="${BUILD_PATH}/ios"
#readonly _CUR_DIR="$(dirname "$0")/.."

#readonly _CUR_DIR="$(dirname "$(readlink "$0")")/.."
#echo "current dir $_CUR_DIR"
#
#if command -v 'pyenv' &> /dev/null
#then
#    eval "$(pyenv init -)"
#    pyenv shell 3.8.3
#    python --version
#fi



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
    echo "${ANDROID_PATH}"
    setup_clean_repo "${ANDROID_PATH}"
    docker run --entrypoint "update-version.sh" --rm -it -v "${ANDROID_PATH}/${PROJECT_NAME}":/project andarius/app-utils:latest --version /project/version
    echo "${RELEASE_KEYSTORE}" | base64 -d > android/app/obitrain.keystore
    cd android
    # ./gradlew assembleRelease
    ./gradlew bundleRelease
else
    echo 'Building iOS'
    setup_clean_repo "${IOS_PATH}"
    cd ios
    pod install
    # Building app
    echo 'Archiving app'
    archive_ios
    # Export the .ipa
    echo 'Exporting ipa'
    xcodebuild -exportArchive -archivePath "$PWD/build/${CI_PROJECT_NAME}.xcarchive" \
               -exportOptionsPlist exportOptions.plist \
               -exportPath "$PWD/build"
fi
