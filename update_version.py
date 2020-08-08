import argparse
from pathlib import Path
from app.changelog import parse_markdown
from app.utils import CONSOLE
import re


def main(options):
    versions = parse_markdown(options['path'])
    project = Path(options['project'])
    build_file = project / 'android' / 'app' / 'build.gradle'

    last_version = versions[0]['version']
    CONSOLE.info('Last version found: ', last_version)

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

    CONSOLE.info('Build file updated @', build_file)
    if options['version']:
        with open(options['version'], 'w') as f:
            f.write(last_version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Update app version in build/gradle file')
    parser.add_argument('-p', '--path',
                        help='Changelog path',
                        required=True)
    parser.add_argument('--project', help='Path to the RN project', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', help='Path where to store the version built')

    options = parser.parse_args()
    main(vars(options))
