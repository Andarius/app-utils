import re
from pathlib import Path
from typing import Literal

from piou import Option

from app_utils.jobs.changelog import parse_markdown, Release
from app_utils.logs import logger


def update_android_version(project: Path, versions: list[Release],
                           output_version: Path | None = None):
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
        output_version.write_text(last_version)


def update_ios_version(project: Path,
                       releases: list[Release],
                       output_version: Path | None = None):
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
        output_version.write_text(last_release.version)


AppType = Literal['ios', 'android']


def run_update_version(
        app_type: AppType = Option(..., '--type', help='Type of the app to update the version'),
        changelog: Path = Option('/project/CHANGELOG.md', '--changelog',
                                 help='Changelog path'),
        project_path: Path = Option('/project', '--project',
                                    help='Path to the RN project'),
        version_path: Path | None = Option(None, '--version', help='Path where to store the version built'),
):
    """
    Utility to update the version depending on the platform using the CHANGELOG.md file:
     - **Android**: updates the versionMajor/Minor/Patch in *app/build.gradle*
     - **iOS**: updates the MARKETING_VERSION and CURRENT_PROJECT_VERSION *ios/app.xcodeproj/project.pbxproj*
    """

    versions = parse_markdown(changelog)
    match app_type:
        case 'android':
            update_android_version(project_path, versions, version_path)
        case 'ios':
            update_ios_version(project_path, versions, version_path)
        case _:
            raise NotImplementedError(f'Got invalid app_type {app_type!r}')
