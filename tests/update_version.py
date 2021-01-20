from .conftest import DATA_FOLDER


def test_upate_version(tmp_folder, project_path):
    from update_version import main

    options = {
        'changelog': DATA_FOLDER / 'CHANGELOG.md',
        'project': project_path,
        'verbose': False,
        'version': tmp_folder / 'version'
    }

    main(options)

    with open(project_path / 'android' / 'app' / 'build.gradle', 'r') as f:
        lines = [x.strip() for i, x in enumerate(f.readlines()) if i < 10]

    assert lines[2] == 'ext.versionMajor = 0'
    assert lines[3] == 'ext.versionMinor = 4'
    assert lines[4] == 'ext.versionPatch = 23'

    with open(tmp_folder / 'version', 'r') as f:
        version = f.read()
    assert version == '0.4.23'
