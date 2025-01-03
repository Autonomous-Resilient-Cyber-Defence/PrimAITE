# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import datetime as datetime
import logging
import logging.config
import shutil
import sys
from bisect import bisect
from logging import Formatter, Logger, LogRecord, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Final, List

import pkg_resources
import yaml
from platformdirs import PlatformDirs

with open(Path(__file__).parent.resolve() / "VERSION", "r") as file:
    __version__ = file.readline().strip()

_PRIMAITE_ROOT: Path = Path(__file__).parent
# TODO: Remove once we integrate the simulation into PrimAITE and it uses the primaite session path


class _PrimaitePaths:
    """
    A Primaite paths class that leverages PlatformDirs.

    The PlatformDirs appname is 'primaite' and the version is ``primaite.__version__`.
    """

    def __init__(self) -> None:
        self._dirs: Final[PlatformDirs] = PlatformDirs(appname="primaite", version=__version__)
        self.user_home_path = self.generate_user_home_path()
        self.user_sessions_path = self.generate_user_sessions_path()
        self.user_config_path = self.generate_user_config_path()
        self.user_notebooks_path = self.generate_user_notebooks_path()
        self.app_home_path = self.generate_app_home_path()
        self.app_config_dir_path = self.generate_app_config_dir_path()
        self.app_config_file_path = self.generate_app_config_file_path()
        self.app_log_dir_path = self.generate_app_log_dir_path()
        self.app_log_file_path = self.generate_app_log_file_path()
        self.episode_log_file_path = self.generate_episode_log_file_path()

    def _get_dirs_properties(self) -> List[str]:
        class_items = self.__class__.__dict__.items()
        return [k for k, v in class_items if isinstance(v, property)]

    def mkdirs(self) -> None:
        """
        Creates all Primaite directories.

        Does this by retrieving all properties in the PrimaiteDirs class and calls each one.
        """
        for p in self._get_dirs_properties():
            getattr(self, p)

    def generate_user_home_path(self) -> Path:
        """The PrimAITE user home path."""
        path = Path.home() / "primaite" / __version__
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_user_sessions_path(self) -> Path:
        """The PrimAITE user sessions path."""
        path = self.user_home_path / "sessions"
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_user_config_path(self) -> Path:
        """The PrimAITE user config path."""
        path = self.user_home_path / "config"
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_user_notebooks_path(self) -> Path:
        """The PrimAITE user notebooks path."""
        path = self.user_home_path / "notebooks"
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_app_home_path(self) -> Path:
        """The PrimAITE app home path."""
        path = self._dirs.user_data_path
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_app_config_dir_path(self) -> Path:
        """The PrimAITE app config directory path."""
        path = self._dirs.user_config_path
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_app_config_file_path(self) -> Path:
        """The PrimAITE app config file path."""
        return self.app_config_dir_path / "primaite_config.yaml"

    def generate_app_log_dir_path(self) -> Path:
        """The PrimAITE app log directory path."""
        if sys.platform == "win32":
            path = self.app_home_path / "logs"
        else:
            path = self._dirs.user_log_path
        path.mkdir(exist_ok=True, parents=True)
        return path

    def generate_app_log_file_path(self) -> Path:
        """The PrimAITE app log file path."""
        return self.app_log_dir_path / "primaite.log"

    def generate_episode_log_file_path(self) -> Path:
        """The PrimAITE app episode step log file path."""
        date_string = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        self.episode_log_dir_path = self.app_log_dir_path / date_string
        self.episode_log_dir_path.mkdir(exist_ok=True, parents=True)
        return self.episode_log_dir_path / "episode.log"

    def __repr__(self) -> str:
        properties_str = ", ".join([f"{p}='{getattr(self, p)}'" for p in self._get_dirs_properties()])
        return f"{self.__class__.__name__}({properties_str})"


PRIMAITE_PATHS: Final[_PrimaitePaths] = _PrimaitePaths()


def _get_primaite_config() -> Dict:
    config_path = PRIMAITE_PATHS.app_config_file_path
    if not config_path.exists():
        # load from package if config does not exist
        config_path = Path(pkg_resources.resource_filename("primaite", "setup/_package_data/primaite_config.yaml"))
        # generate app config
        shutil.copy2(config_path, PRIMAITE_PATHS.app_config_file_path)
    with open(config_path, "r") as file:
        # load from config
        primaite_config = yaml.safe_load(file)
        return primaite_config


PRIMAITE_CONFIG = _get_primaite_config()


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


_LEVEL_FORMATTER: Final[_LevelFormatter] = _LevelFormatter(
    {
        logging.DEBUG: PRIMAITE_CONFIG["logging"]["logger_format"]["DEBUG"],
        logging.INFO: PRIMAITE_CONFIG["logging"]["logger_format"]["INFO"],
        logging.WARNING: PRIMAITE_CONFIG["logging"]["logger_format"]["WARNING"],
        logging.ERROR: PRIMAITE_CONFIG["logging"]["logger_format"]["ERROR"],
        logging.CRITICAL: PRIMAITE_CONFIG["logging"]["logger_format"]["CRITICAL"],
    }
)

_STREAM_HANDLER: Final[StreamHandler] = StreamHandler()

_FILE_HANDLER: Final[RotatingFileHandler] = RotatingFileHandler(
    filename=PRIMAITE_PATHS.app_log_file_path,
    maxBytes=10485760,  # 10MB
    backupCount=9,  # Max 100MB of logs
    encoding="utf8",
)
_STREAM_HANDLER.setLevel(PRIMAITE_CONFIG["logging"]["log_level"])
_FILE_HANDLER.setLevel(PRIMAITE_CONFIG["logging"]["log_level"])

_LOG_FORMAT_STR: Final[str] = PRIMAITE_CONFIG["logging"]["logger_format"]
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
    logger.setLevel(PRIMAITE_CONFIG["logging"]["log_level"])

    return logger


DEFAULT_BANDWIDTH: Final[int] = 100
