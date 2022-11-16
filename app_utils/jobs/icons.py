import logging
from collections import namedtuple
from pathlib import Path

import cairosvg
from piou import Option

Sizes = namedtuple('Sizes', ['size', 'formats'])

_DEFAULT_SIZES = {
    '': Sizes(28, [1, 2, 3]),
    '.android': Sizes(22, [1, 2, 3, 4])
}


def run_icons(
        icons_folder: Path | None = Option(None, '--folder', help='Folder containing svg icons to convert'),
        icon: Path | None = Option(None, '-f', '--file', help='Svg icon to convert'),
        output_folder=Option(..., '-o', '--output', help='Folder where to write the output')
):
    files = []
    if icons_folder:
        files += list(icons_folder.glob('*.svg'))
    if icon:
        files = [icon]

    if not files:
        logging.error('Please specify either --folder or --file')
        return

    for file in files:
        for ext, _default_size in _DEFAULT_SIZES.items():
            for _format in _default_size.formats:
                _file_ext = (f'@{_format}x' if _format > 1 else '') + ext
                _output_file = file.name.replace(file.suffix, '') + _file_ext + '.png'
                output_size = _default_size.size * _format
                print(f'\tsize: {output_size:<4} | ext: {_file_ext}')
                cairosvg.svg2png(url=str(file),
                                 output_height=output_size,
                                 output_width=output_size,
                                 write_to=str(output_folder / _output_file))
