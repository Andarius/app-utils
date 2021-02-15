"""
First, to get the size of the image run
    identify path-to-my-image | awk '{print $3}'
Then
    python crop.py -f ~/Downloads/Screenshots --dim "1080x2400" -t 117 -b 125
"""
import argparse
from pathlib import Path
from typing import List
import shutil
import subprocess

parser = argparse.ArgumentParser('Crop images')
parser.add_argument('-f', '--folder',
                    required=True,
                    type=Path, help='Path of the folder containing the images to crop')
parser.add_argument('-o', '--output',
                    # required=True,
                    type=Path, help='Path where the crop images will be ')
parser.add_argument('--extensions',
                    nargs='+',
                    default=['png', 'jpg'],
                    help='Extension file to look for')
parser.add_argument('-t', '--top', type=int,
                    default=0,
                    help='Crop from the top')
parser.add_argument('-b', '--bottom', type=int,
                    default=0,
                    help='Crop from the top')
parser.add_argument('--dim', type=str, required=True, help='Images dimensions of the form WxH')


def crop_image(input_path, output_path, crop_dim):
    process = subprocess.Popen(['convert', input_path, '-crop', crop_dim, output_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        raise OSError(stderr.decode('utf-8'))


def main(folder: Path,
         output_folder: Path,
         extensions: List[str],
         image_dim: str,
         from_top: int = 0,
         from_bottom: int = 0):
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
            crop_image(p, _file_output, crop_dim)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.folder, args.output, args.extensions,
         args.dim, args.top, args.bottom)
