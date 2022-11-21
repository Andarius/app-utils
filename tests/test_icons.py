def test_create_icons(static_folder, tmp_path, monkeypatch):
    from app_utils.jobs.icons import run_icons

    svg_path = static_folder / 'test.svg'

    run_icons(icon=svg_path,
              icons_folder=None,
              output_folder=tmp_path)
    assert list(tmp_path.glob('*.png'))
