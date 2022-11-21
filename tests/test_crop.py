def test_crop_image(static_folder, tmp_path, monkeypatch):
    def crop_image_mock(input_path, output_path, crom_dim):
        return

    monkeypatch.setattr('app_utils.jobs.crop.crop_image',
                        crop_image_mock)
    from app_utils.jobs.crop import run_crop

    run_crop(static_folder, output_folder=tmp_path,
             extensions=['jpeg'],
             image_dim='100x100',
             from_top=10,
             from_bottom=20)
