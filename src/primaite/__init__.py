# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import logging
import logging.config
import sys
from logging import Logger, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

from platformdirs import PlatformDirs

_PLATFORM_DIRS: Final[PlatformDirs] = PlatformDirs(appname="primaite")
"""An instance of `PlatformDirs` set with appname='primaite'."""

_USER_DIRS: Final[Path] = Path.home() / "primaite"
"""The users home space for PrimAITE which is located at: ~/primaite."""

NOTEBOOKS_DIR: Final[Path] = _USER_DIRS / "notebooks"
"""
The path to the users notebooks directory as an instance of `Path` or
`PosixPath`, depending on the OS.

Users notebooks are stored at: ``~/primaite/notebooks``.
"""

USERS_CONFIG_DIR: Final[Path] = _USER_DIRS / "config"
"""
The path to the users config directory as an instance of `Path` or
`PosixPath`, depending on the OS.

Users config files are stored at: ``~/primaite/config``.
"""

SESSIONS_DIR: Final[Path] = _USER_DIRS / "sessions"
"""
The path to the users PrimAITE Sessions directory as an instance of `Path` or
`PosixPath`, depending on the OS.

Users PrimAITE Sessions are stored at: ``~/primaite/sessions``.
"""


# region Setup Logging
def _log_dir() -> Path:
    if sys.platform == "win32":
        dir_path = _PLATFORM_DIRS.user_data_path / "logs"
    else:
        dir_path = _PLATFORM_DIRS.user_log_path
    return dir_path


LOG_DIR: Final[Path] = _log_dir()
"""The path to the app log directory as an instance of `Path` or `PosixPath`, depending on the OS."""

LOG_DIR.mkdir(exist_ok=True, parents=True)

LOG_PATH: Final[Path] = LOG_DIR / "primaite.log"
"""The primaite.log file path as an instance of `Path` or `PosixPath`, depending on the OS."""

_STREAM_HANDLER: Final[StreamHandler] = StreamHandler()
_FILE_HANDLER: Final[RotatingFileHandler] = RotatingFileHandler(
    filename=LOG_PATH,
    maxBytes=10485760,  # 10MB
    backupCount=9,  # Max 100MB of logs
    encoding="utf8",
)
_STREAM_HANDLER.setLevel(logging.INFO)
_FILE_HANDLER.setLevel(logging.INFO)

_LOG_FORMAT_STR: Final[
    str
] = "%(asctime)s::%(levelname)s::%(name)s::%(lineno)s::%(message)s"
_STREAM_HANDLER.setFormatter(logging.Formatter(_LOG_FORMAT_STR))
_FILE_HANDLER.setFormatter(logging.Formatter(_LOG_FORMAT_STR))

_LOGGER = logging.getLogger(__name__)

_LOGGER.addHandler(_STREAM_HANDLER)
_LOGGER.addHandler(_FILE_HANDLER)


def getLogger(name: str) -> Logger:
    """
    Get a PrimAITE logger.

    :param name: The logger name. Use ``__name__``.
    :return: An instance of :py:class:`logging.Logger` with the PrimAITE
        logging config.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    return logger


# endregion


with open(Path(__file__).parent.resolve() / "VERSION", "r") as file:
    __version__ = file.readline()
