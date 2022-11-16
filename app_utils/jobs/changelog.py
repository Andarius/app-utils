import re
from dataclasses import dataclass, asdict, field
from pathlib import Path

from piou import Option

from app_utils.logs import logger

_version_reg = re.compile(r'^##\s+\[v(?P<version>\d+\.\d+\.\d+)\]$')
_lang_reg = re.compile(r'-\s+\*\*(?P<lang>\w{2}\-\w{2})\*\*:')

_header_reg = re.compile(r'###\s+[^\w]*\s*(?P<header>[\w\s]+)',
                         flags=re.UNICODE)
_remove_extra_spaces_reg = re.compile(r'\s{2,}')


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
    release_notes: list[ReleaseNote] = field(default_factory=list)

    @property
    def version_code(self) -> int:
        major, minor, patch = self.version.split('.')
        return int(major) * 1000000 + int(minor) * 1000 + int(patch)

    @property
    def data(self):
        return asdict(self)

    def __post_init__(self):
        self.release_notes = [ReleaseNote(**x)
                              if isinstance(x, dict) else x
                              for x in self.release_notes]


def parse_markdown(path: Path) -> list[Release]:
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
        logger.error(f'No file found @ {file}')

    with open(file, 'r') as f:
        lines = [x.strip() for x in f.readlines() if x.strip()]

    versions = []
    current_version = {}
    current_lang = {}

    for l in lines:
        if l.startswith('## '):
            _reset()
            version = _version_reg.match(l)
            if version is None:
                raise ValueError(f'No match found for line {l!r}')
            current_version['version'] = version.group('version')
            current_version['languages'] = []

        if current_version:
            lang = _lang_reg.match(l)

            if lang:
                _reset_lang()
                current_lang = {'lang': lang.group('lang'), 'lines': []}
            elif current_lang:
                current_lang['lines'].append(_remove_extra_spaces_reg.sub(' ', l))

    _reset()

    return [Release(version=x['version'],
                    release_notes=[ReleaseNote(language=lang['lang'], text=lang['text']) for lang in
                                   x.pop('languages')])
            for x in versions]


def print_release_infos(release: Release):
    print('[bold]version:[/bold]', release.version)
    print('[bold]version_code:[/bold]', release.version_code)
    if release.release_notes:
        for notes in release.release_notes:
            print(f'<{notes.language}>')
            print(notes.html_text)
            print(f'</{notes.language}>')
    else:
        print('No release notes')


def run_changelog(
        path: Path = Option(..., '--path', '-p', help='Changelog path'),
        show_last: bool = Option(False, '-l', '--last', help='Prints the last version'),
        show_releases: bool = Option(False, '-a', '--all-releases', help='Prints all available releases'),
        release_version: bool = Option(False, '-r', '--release', help='Release version')
):
    releases = parse_markdown(path)
    if show_last:
        print_release_infos(releases[0])
    elif show_releases:
        for release in releases:
            print(release.version)
    elif release_version:
        release = [x for x in releases if x.version == release_version]
        if release:
            print_release_infos(release[0])
        else:
            print('[red]release not found[/red]')
    else:
        print('[red]Nothing to do[/red]')
