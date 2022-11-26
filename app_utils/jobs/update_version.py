import re
import sys
from pathlib import Path
from typing import Literal

from piou import Option

from app_utils.jobs.changelog import parse_markdown
from app_utils.logs import logger


def update_android_version(project: Path, version: str):
    build_file = project / 'android' / 'app' / 'build.gradle'

    logger.info(f'Last version found: {version}')

    _major, _minor, _patch = version.split('.')
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


_MARKET_VERSION_REG = re.compile(r'(MARKETING_VERSION) = \d+\.\d+(\.\d+)?;')
_CURRENT_PROJECT_VERSION_REG = re.compile(r'(CURRENT_PROJECT_VERSION) = \d+;')


def update_ios_version(project: Path,
                       version: str,
                       version_code: int,
                       project_name: str):
    pbxproj_path = project / 'ios' / f'{project_name}.xcodeproj' / 'project.pbxproj'

    _major, _minor, _patch = version.split('.')
    text = pbxproj_path.read_text()

    if not _MARKET_VERSION_REG.findall(text):
        raise NotImplementedError(f'Could not find MARKETING_VERSION in {pbxproj_path!r}')
    text = _MARKET_VERSION_REG.sub(fr'\1 = {_major}.{_minor}.{_patch};', text)

    if not _CURRENT_PROJECT_VERSION_REG.findall(text):
        raise NotImplementedError(f'Could not find CURRENT_PROJECT_VERSION in {pbxproj_path!r}')
    text = _CURRENT_PROJECT_VERSION_REG.sub(fr'\1 = {version_code};', text)

    pbxproj_path.write_text(text)
    logger.info(f'Project.pbxproj updated @{pbxproj_path}')


AppType = Literal['ios', 'android']


def run_update_version(
        app_type: AppType = Option(..., '--type', help='Type of the app to update the version'),
        changelog: Path = Option('/project/CHANGELOG.md', '--changelog',
                                 help='Changelog path'),
        project_path: Path = Option('/project', '--project',
                                    help='Path to the RN project'),
        project_name: str | None = Option(None, '--name',
                                          help='Project name (iOS only)'),
        version_path: str | None = Option(None, '--version', help='Path where to store the version built'),
):
    """
    Utility to update the version depending on the platform using the CHANGELOG.md file:
     - **Android**: updates the versionMajor/Minor/Patch in *app/build.gradle*
     - **iOS**: updates the MARKETING_VERSION and CURRENT_PROJECT_VERSION *ios/app.xcodeproj/project.pbxproj*
    """

    releases = parse_markdown(changelog)

    output_version = Path(version_path) if version_path else None

    last_release = releases[0]
    last_version = last_release.version
    match app_type:
        case 'android':
            update_android_version(project_path, version=last_version)
        case 'ios':
            if project_name is None:
                logger.error('Please specify a project name (--name)')
                sys.exit(1)
            update_ios_version(project_path, version=last_release.version,
                               version_code=last_release.version_code,
                               project_name=project_name)
        case _:
            raise NotImplementedError(f'Got invalid app_type {app_type!r}')

    if output_version:
        logger.info(f'Creating version file @{output_version} ({last_version})')
        output_version.write_text(last_version)
