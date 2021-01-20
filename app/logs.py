import logging
from pathlib import Path
from rich.logging import RichHandler

logger = logging.getLogger('app-utils')

_LOG_FORMAT = "[%(filename)s] %(message)s"


def init_logging(log_lvl=logging.INFO,
                 logs_path=None
                 ):
    handlers = [
        RichHandler(rich_tracebacks=True)
    ]
    if logs_path is not None:
        handlers.append(logging.FileHandler(logs_path))
    logging.basicConfig(
        level=log_lvl.upper() if isinstance(log_lvl, str) else log_lvl,
        # format=_LOG_FORMAT,
        datefmt="%y%m%d %H:%M:%S",
        format="%(message)s",
        handlers=handlers
    )
