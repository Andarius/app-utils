import argparse
import cairosvg
from pathlib import Path
from app.utils import CONSOLE
from collections import namedtuple

Sizes = namedtuple('Sizes', ['size', 'formats'])

_DEFAULT_SIZES = {
    '': Sizes(28, [1, 2, 3]),
    '.android': Sizes(22, [1, 2, 3, 4])
}


parser = argparse.ArgumentParser()
parser.add_argument('--folder', help='Folder containing svg icons to convert')
parser.add_argument('-f', '--file', help='Svg icon to convert')
parser.add_argument('-o', '--output', help='Folder where to write the output', required=True)


def main(options):
    files = list(Path(options.folder).glob('*.svg')) if options.folder else [Path(options.file)]
    output_path = Path(options.output)

    for file in files:
        CONSOLE.info(file)
        for ext, _default_size in _DEFAULT_SIZES.items():
            for _format in _default_size.formats:
                _file_ext = (f'@{_format}x' if _format > 1 else '') + ext
                _output_file = file.name.replace(file.suffix, '') + _file_ext + '.png'
                output_size = _default_size.size * _format
                CONSOLE.info(f'\tsize: {output_size:<4} | ext: {_file_ext}')
                cairosvg.svg2png(url=str(file),
                                 output_height=output_size,
                                 output_width=output_size,
                                 write_to=str(output_path / _output_file))


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
