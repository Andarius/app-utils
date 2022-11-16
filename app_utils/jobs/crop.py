import shutil
from pathlib import Path

from piou import Option

from app_utils.utils import exec_cmd


def crop_image(input_path: str, output_path: str, crop_dim: str):
    """
    Make sure you have imagemagick installed https://imagemagick.org/script/download.php#linux
    """
    exec_cmd(['convert', input_path, '-crop', crop_dim, output_path])


def run_crop(
        folder: Path = Option(..., '-f', '--folder', help='Path of the folder containing the images to crop'),
        output_folder: Path = Option(..., '-o', '--output', help='Path where the crop images will be '),
        extensions: list[str] = Option(['png', 'jpg'], '--extensions', help='Extension file to look for'),
        image_dim: str = Option(..., '--dim', help='Images dimensions of the form WxH'),
        from_top: int = Option(0, '-t', '--top', help='Crop from the top'),
        from_bottom: int = Option(0, '-b', '--bottom', help='Crop from the top'),
):
    """
    First, to get the size of the image run
        identify path-to-my-image | awk '{print $3}'
    Then
        python crop.py -f ~/Downloads/Screenshots --dim "1080x2400" -t 117 -b 125

    Formats:
        "1080x2400":  -t 117 -b 125
        "1080x2340":  -t 64  -b 132
    """
    if not folder.exists():
        raise FileNotFoundError('Input folder does not exists')

    output_folder = output_folder or folder.parent / (folder.name + '_cropped')
    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(exist_ok=False)

    _width, _heigth = image_dim.split('x')
    crop_dim = f'{_width}x{int(_heigth) - from_bottom - from_top}+0+{from_top}'

    for ext in extensions:
        for p in folder.glob(f'**/*.{ext}'):
            _file_output = Path(str(p).replace(str(folder), str(output_folder)))
            if not _file_output.parent.exists():
                _file_output.parent.mkdir(parents=True)
            crop_image(str(p), str(_file_output), crop_dim)
