import argparse
from pathlib import Path
import re
import pprint

from .utils import CONSOLE

_version_reg = re.compile(r'^## \[v(?P<version>\d+\.\d+\.\d+)\]$')
_lang_reg = re.compile(r'- \*\*(?P<lang>\w{2}\-\w{2})\*\*:')


def parse_markdown(file: Path):

    def _reset_lang():
        nonlocal current_lang
        if current_version and current_lang:
            current_lang['text'] = '\n'.join(current_lang.pop('lines'))
            current_version['languages'].append(current_lang)
        current_lang = {}

    def _reset():
        nonlocal current_version
        _reset_lang()
        if current_version:
            versions.append(current_version)
            current_version = {}

    if not file.exists():
        CONSOLE.error(f'No file found @ {file}')

    with open(file, 'r') as f:
        lines = [x.strip() for x in f.readlines() if x.strip()]

    versions = []
    current_version = {}
    current_lang = {}

    for l in lines:
        if l.startswith('## '):
            _reset()

            version = _version_reg.match(l)
            current_version['version'] = version.group('version')
            current_version['languages'] = []

        if current_version:
            lang = _lang_reg.match(l)

            if lang:
                _reset_lang()
                current_lang = {'lang': lang.group('lang'), 'lines': []}
            elif current_lang:
                current_lang['lines'].append(l)

    _reset()

    return versions


def main(options):
    file = Path(options.pop('path'))
    data = parse_markdown(file)

    pprint.pprint(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Changelog parser')
    parser.add_argument('-p', '--path',
                        help='Changelog path',
                        required=True)
    parser.add_argument('-v', '--verbose', action='store_true')

    options = parser.parse_args()
    main(vars(options))
