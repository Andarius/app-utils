"""
Utility to update the version depending on the platform using the CHANGELOG.md file:
 - **Android**: updates the versionMajor/Minor/Patch in *app/build.gradle*
 - **iOS**: updates the MARKETING_VERSION and CURRENT_PROJECT_VERSION *ios/app.xcodeproj/project.pbxproj*
"""
import argparse
import logging
from typing import List
from pathlib import Path
from app.changelog import parse_markdown, Release
from app.logs import logger, init_logging
import re


def update_android_version(project: Path, versions: List[Release], output_version: str = None):
    build_file = project / 'android' / 'app' / 'build.gradle'

    last_version = versions[0].version
    logger.info(f'Last version found: {last_version}')

    _major, _minor, _patch = last_version.split('.')
    text = build_file.read_text()
    replacements = [
        ('ext.versionMajor', _major),
        ('ext.versionMinor', _minor),
        ('ext.versionPatch', _patch)
    ]

    for _to_replace, _version in replacements:
        text = re.sub(rf'{re.escape(_to_replace)} = \d+', f'{_to_replace} = {_version}', text)

    build_file.write_text(text)

    logger.info(f'Build file updated @{build_file}')
    if output_version:
        logger.info(f'Creating version file @{output_version}')
        with open(output_version, 'w') as f:
            f.write(last_version)


def update_ios_version(project: Path, releases: List[Release], output_version: str = None):
    pbxproj_path = project / 'ios' / f'{project.name}.xcodeproj' / 'project.pbxproj'
    last_release = releases[0]
    logger.info(f'Last version found: {last_release.version}')

    _major, _minor, _patch = last_release.version.split('.')
    text = pbxproj_path.read_text()
    text = re.sub(r'(MARKETING_VERSION) = \d+\.\d+(\.\d+)?;', fr'\1 = {_major}.{_minor}.{_patch};', text)
    text = re.sub(r'(CURRENT_PROJECT_VERSION) = \d+;', fr'\1 = {last_release.version_code};', text)

    pbxproj_path.write_text(text)
    logger.info(f'Project.pbxproj updated @{pbxproj_path}')
    if output_version:
        logger.info(f'Creating version file @{output_version}')
        with open(output_version, 'w') as f:
            f.write(last_release.version)


def main(options):
    project = Path(options['project'])
    versions = parse_markdown(options['changelog'])
    if options['type'] == 'android':
        update_android_version(project, versions, options.get('version'))
    elif options['type'] == 'ios':
        update_ios_version(project, versions, options.get('version'))
    else:
        print('nothing to')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Update app version in build/gradle file')
    parser.add_argument('--changelog',
                        help='Changelog path',
                        default='/project/CHANGELOG.md')
    parser.add_argument('--project',
                        default='/project',
                        help='Path to the RN project')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', help='Path where to store the version built')
    parser.add_argument('--type', choices=['android', 'ios'])
    parser.add_argument('--log-lvl', type=str, default=None)

    options = parser.parse_args()
    init_logging(log_lvl=options.log_lvl.upper() if options.log_lvl
    else (logging.INFO if options.verbose else logging.WARNING)
                 )
    main(vars(options))
