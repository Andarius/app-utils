import pytest
from .conftest import DATA_FOLDER
from dataclasses import asdict




@pytest.mark.parametrize('path', [
    DATA_FOLDER / 'CHANGELOG.md'
])
def test_parse_markdown(path):
    from app.changelog import parse_markdown
    results = parse_markdown(path)
    assert [asdict(x) for x in results] == [
        {'release_notes': [{'language': 'fr-FR',
                            'text': '### 🐛 Bugs réparés\n'
                                    '- Bug lors de la mise à jour de la séance'},
                           {'language': 'en-US',
                            'text': '### 🐛 Bug fixed\n- Bug during session update'}],
         'version': '0.4.23'},
        {'release_notes': [{'language': 'fr-FR',
                            'text': '### 🐛 Bugs réparés\n'
                                    "- Bug lors de la création d'une séance"},
                           {'language': 'en-US',
                            'text': '### 🐛 Bug fixed\n- Bug during session creation'}],
         'version': '0.4.22'},
        {'release_notes': [{'language': 'fr-FR',
                            'text': '### Nouveautés\n'
                                    "- Possibilité de voir et d'utiliser les "
                                    'exercices de ses amis'},
                           {'language': 'en-US',
                            'text': '### 🔥 New\n'
                                    '- You can now see and use your friends '
                                    'exercises'}],
         'version': '0.4.21'}]


@pytest.mark.parametrize('data, expected', [
    ({'version': '4.0.1', 'release_notes': [{'language': 'FR-fr', 'text': '### 🐛 Bug fixed\n- Bug during session update'}]},
     {'version_code': 4000001, 'html': "🐛 <b>Bug fixed</b>\n- Bug during session update"})
])
def test_release(data, expected):
    from app.changelog import Release
    release = Release(**data)
    assert release.version_code == expected['version_code']
    assert release.release_notes[0].html_text == expected['html']
