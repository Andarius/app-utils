import argparse
from pathlib import Path
import re
import pprint
from typing import Union, List
from dataclasses import dataclass, asdict

from .utils import CONSOLE

_version_reg = re.compile(r'^## \[v(?P<version>\d+\.\d+\.\d+)\]$')
_lang_reg = re.compile(r'- \*\*(?P<lang>\w{2}\-\w{2})\*\*:')

_header_reg = re.compile(r'###\s?.\s?(?P<header>[\w\s]+)')


@dataclass
class ReleaseNote:
    language: str
    text: str

    @property
    def html_text(self):
        text = self.text
        matches = [x.strip() for x in _header_reg.findall(self.text)]

        for match in matches:
            text = text.replace(match, f'<b>{match}</b>').replace('### ', '')
        return text

    @property
    def data(self):
        return {
            'language': self.language,
            'text': self.html_text
        }


@dataclass
class Release:
    version: str
    release_notes: List[ReleaseNote]

    @property
    def version_code(self) -> int:
        major, minor, patch = self.version.split('.')
        return int(major) * 1000000 + int(minor) * 1000 + int(patch)

    @property
    def data(self):
        return asdict(self)


def parse_markdown(path: Union[Path, str]) -> List[Release]:
    file = path if isinstance(str, Path) else Path(path)

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

    return [Release(version=x['version'],
                    release_notes=[ReleaseNote(language=lang['lang'], text=lang['text']) for lang in
                                   x.pop('languages')])
            for x in versions]


def main(options):
    data = parse_markdown(options['path'])
    if options['last']:
        print('version:', data[0].version)
        print('version_code:', data[0].version_code)
    else:
        print(data[0].release_notes[0].html_text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Changelog parser')
    parser.add_argument('-p', '--path',
                        help='Changelog path',
                        required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--last', action='store_true', help='Will print the last version')

    options = parser.parse_args()
    main(vars(options))
