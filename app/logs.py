import logging
from pathlib import Path
from rich.logging import RichHandler


logger = logging.getLogger('app-utils')

_LOG_FORMAT = "[%(filename)s] %(message)s"


def init_logging(logs_path='/logs',
                 log_lvl=logging.INFO):
    fh = logging.FileHandler(Path(logs_path) / 'logs.log') if logs_path else None
    logging.basicConfig(
        level=log_lvl.upper() if isinstance(log_lvl, str) else log_lvl,
        # format=_LOG_FORMAT,
        datefmt="%y%m%d %H:%M:%S",
        format="%(message)s",
        handlers=[
            fh,
            RichHandler(rich_tracebacks=True)
        ]
    )