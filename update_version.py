import argparse
import logging
from pathlib import Path
from app.changelog import parse_markdown
from app.logs import logger, init_logging
import re


def main(options):
    versions = parse_markdown(options['changelog'])
    project = Path(options['project'])
    build_file = project / 'android' / 'app' / 'build.gradle'

    last_version = versions[0].version
    logger.info('Last version found: ', last_version)

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

    logger.info('Build file updated @', build_file)
    version_file = options.get('version')
    if version_file:
        logger.info('Creating version file @', version_file)
        with open(version_file, 'w') as f:
            f.write(last_version)


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

    options = parser.parse_args()
    init_logging(log_lvl=logging.INFO if options.verbose else logging.WARNING)
    main(vars(options))
