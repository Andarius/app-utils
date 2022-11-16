import logging

from rich.logging import RichHandler

logger = logging.getLogger('app-utils')


def init_logging():
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=False, show_path=False)]
    )
