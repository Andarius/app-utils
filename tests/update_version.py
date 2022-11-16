from .conftest import DATA_FOLDER


def test_update_version_android(tmp_path, project_path):
    from app_utils.jobs.update_version import run_update_version

    run_update_version(
        app_type='android',
        changelog=DATA_FOLDER / 'CHANGELOG.md',
        project_path=project_path,
        version_path=tmp_path / 'version',
    )

    with open(project_path / 'android' / 'app' / 'build.gradle', 'r') as f:
        lines = [x.strip() for i, x in enumerate(f.readlines()) if i < 10]

    assert lines[2] == 'ext.versionMajor = 0'
    assert lines[3] == 'ext.versionMinor = 4'
    assert lines[4] == 'ext.versionPatch = 23'

    with open(tmp_path / 'version', 'r') as f:
        version = f.read()
    assert version == '0.4.23'


def test_update_version_ios(tmp_path, project_path):
    from app_utils.jobs.update_version import run_update_version

    run_update_version(
        app_type='ios',
        changelog=DATA_FOLDER / 'CHANGELOG.md',
        project_path=project_path,
        version_path=tmp_path / 'version',
    )

    with open(project_path / 'ios' / 'myApp.xcodeproj' / 'project.pbxproj', 'r') as f:
        lines = [x.strip() for i, x in enumerate(f.readlines())]

    marketing_lines = [x for x in lines if 'MARKETING_VERSION' in x]
    assert marketing_lines
    for _marketing_line in marketing_lines:
        assert _marketing_line == 'MARKETING_VERSION = 0.4.23;'

    curr_prj_lines = [x for x in lines if 'CURRENT_PROJECT_VERSION' in x]
    assert curr_prj_lines
    for _curr_prj_line in curr_prj_lines:
        assert _curr_prj_line == 'CURRENT_PROJECT_VERSION = 4023;'

    assert (tmp_path / 'version').read_text() == '0.4.23'
