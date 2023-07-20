# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
import logging
import logging.config
import sys
from bisect import bisect
from logging import Formatter, Logger, LogRecord, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Final

import pkg_resources
import yaml
from platformdirs import PlatformDirs

_PLATFORM_DIRS: Final[PlatformDirs] = PlatformDirs(appname="primaite")
"""An instance of `PlatformDirs` set with appname='primaite'."""


def _get_primaite_config() -> Dict:
    config_path = _PLATFORM_DIRS.user_config_path / "primaite_config.yaml"
    if not config_path.exists():
        config_path = Path(pkg_resources.resource_filename("primaite", "setup/_package_data/primaite_config.yaml"))
    with open(config_path, "r") as file:
        primaite_config = yaml.safe_load(file)
    log_level_map = {
        "NOTSET": logging.NOTSET,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARN,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    primaite_config["log_level"] = log_level_map[primaite_config["logging"]["log_level"]]
    return primaite_config


_PRIMAITE_CONFIG = _get_primaite_config()

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
class _LevelFormatter(Formatter):
    """
    A custom level-specific formatter.

    Credit to: https://stackoverflow.com/a/68154386
    """

    def __init__(self, formats: Dict[int, str], **kwargs: Any) -> None:
        super().__init__()

        if "fmt" in kwargs:
            raise ValueError("Format string must be passed to level-surrogate formatters, " "not this one")

        self.formats = sorted((level, Formatter(fmt, **kwargs)) for level, fmt in formats.items())

    def format(self, record: LogRecord) -> str:
        """Overrides ``Formatter.format``."""
        idx = bisect(self.formats, (record.levelno,), hi=len(self.formats) - 1)
        level, formatter = self.formats[idx]
        return formatter.format(record)


def _log_dir() -> Path:
    if sys.platform == "win32":
        dir_path = _PLATFORM_DIRS.user_data_path / "logs"
    else:
        dir_path = _PLATFORM_DIRS.user_log_path
    return dir_path


_LEVEL_FORMATTER: Final[_LevelFormatter] = _LevelFormatter(
    {
        logging.DEBUG: _PRIMAITE_CONFIG["logging"]["logger_format"]["DEBUG"],
        logging.INFO: _PRIMAITE_CONFIG["logging"]["logger_format"]["INFO"],
        logging.WARNING: _PRIMAITE_CONFIG["logging"]["logger_format"]["WARNING"],
        logging.ERROR: _PRIMAITE_CONFIG["logging"]["logger_format"]["ERROR"],
        logging.CRITICAL: _PRIMAITE_CONFIG["logging"]["logger_format"]["CRITICAL"],
    }
)

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
_STREAM_HANDLER.setLevel(_PRIMAITE_CONFIG["logging"]["log_level"])
_FILE_HANDLER.setLevel(_PRIMAITE_CONFIG["logging"]["log_level"])

_LOG_FORMAT_STR: Final[str] = _PRIMAITE_CONFIG["logging"]["logger_format"]
_STREAM_HANDLER.setFormatter(_LEVEL_FORMATTER)
_FILE_HANDLER.setFormatter(_LEVEL_FORMATTER)

_LOGGER = logging.getLogger(__name__)

_LOGGER.addHandler(_STREAM_HANDLER)
_LOGGER.addHandler(_FILE_HANDLER)


def getLogger(name: str) -> Logger:  # noqa
    """
    Get a PrimAITE logger.

    :param name: The logger name. Use ``__name__``.
    :return: An instance of :py:class:`logging.Logger` with the PrimAITE
        logging config.
    """
    logger = logging.getLogger(name)
    logger.setLevel(_PRIMAITE_CONFIG["log_level"])

    return logger


# endregion


with open(Path(__file__).parent.resolve() / "VERSION", "r") as file:
    __version__ = file.readline().strip()
