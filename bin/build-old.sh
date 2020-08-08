#!/bin/zsh

# set -xe

export PATH=$PATH:/usr/local/bin:/usr/bin/:${HOME}/miniconda3/bin
export ANDROID_HOME=$HOME/Library/Android/sdk

readonly UTILS_PATH=$HOME/Projects/app-utils

readonly ANDROID_PATH=${BUILD_PATH}/android
readonly IOS_PATH=${BUILD_PATH}/ios

readonly BRANCH='master'

mkdir -p ${ANDROID_PATH} ${IOS_PATH}

setup_clean_repo(){
    rm -rf ${CI_PROJECT_NAME}
    git clone ${CI_REPOSITORY_URL} -b ${BRANCH}
    cd ${CI_PROJECT_NAME}
    python ${UTILS_PATH}/update_version.py -p ${PWD}/CHANGELOG.md --project ${PWD}
    mv /tmp/.env .
    yarn install
}

archive_ios(){
    # Somehow fails 4/5 times usually before executing correctly ...
    # Note: -destination 'platform=iOS Simulator, name=iPhone 7' instead of -sdk iphoneos12.2  seems to work also
    status=1
    counter=1
    while [[ $status != 0 && counter > 10 ]]; do
        xcodebuild -quiet -workspace ${CI_PROJECT_NAME}.xcworkspace \
                   -scheme ${CI_PROJECT_NAME} \
                   -sdk iphoneos12.2  \
                   -configuration AppStoreDistribution \
                   clean archive \
                   -archivePath $PWD/build/${CI_PROJECT_NAME}.xcarchive
        status=$?
        echo "Got status: $status ($counter / 10)"
        counter=$((counter+1))
    done
    echo "Final status: $status"
}

if [[ "$1" = "android" ]]; then
    echo "Building android"
    cd ${ANDROID_PATH}
    setup_clean_repo
    echo "${RELEASE_KEYSTORE}" | base64 --decode > android/app/obitrain.keystore
    cd android
    # ./gradlew assembleRelease
    ./gradlew bundleRelease
else
    echo 'Building iOS'
    cd ${IOS_PATH}
    setup_clean_repo
    cd ios
    pod install
    # Building app
    echo 'Archiving app'
    archive_ios
    # Export the .ipa
    echo 'Exporting ipa'
    xcodebuild -exportArchive -archivePath $PWD/build/${CI_PROJECT_NAME}.xcarchive \
               -exportOptionsPlist exportOptions.plist \
               -exportPath $PWD/build
fi