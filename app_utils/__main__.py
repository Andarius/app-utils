import logging

from piou import Cli

from app_utils.jobs import (
    run_changelog, run_crop, run_update_version, run_icons,
    android
)
from app_utils.logs import init_logging, logger

cli = Cli('Cli utilities for React Native')

cli.add_option('-v', '--verbose', help='Verbosity')
cli.add_option('-vv', '--verbose2', help='Increased verbosity')

cli.add_command('changelog', run_changelog)
cli.add_command('crop', run_crop)
cli.add_command('update-version', run_update_version)
cli.add_command('resize-icons', run_icons)
cli.add_command_group(android)


def on_process(verbose: bool = False, verbose2: bool = False):
    init_logging()
    logger.setLevel(logging.DEBUG if verbose2 else
                    logging.INFO if verbose else
                    logging.WARNING)


cli.set_options_processor(on_process)


def run():
    cli.run()


if __name__ == '__main__':
    run()
