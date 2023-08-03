import logging
from pathlib import Path


class _NotJSONFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter logs that do not start and end with '{' and '}'."""
        return not record.getMessage().startswith("{") and not record.getMessage().endswith("}")


class SysLog:
    """
    A simple logger class for writing the sys logs of a Node.

    Logs are logged to: <simulation output directory>/<hostname>/<hostname>_sys.log
    """

    def __init__(self, hostname: str):
        """
        Initialize the SysLog instance.

        :param hostname: The hostname for which logs are being recorded.
        """
        self.hostname = hostname
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger configuration."""
        log_path = self._get_log_path()

        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(logging.DEBUG)

        log_format = "%(asctime)s %(levelname)s: %(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        self.logger = logging.getLogger(f"{self.hostname}_sys_log")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        self.logger.addFilter(_NotJSONFilter())

    def _get_log_path(self) -> Path:
        """Get the path for the log file."""
        root = Path(__file__).parent.parent.parent.parent.parent.parent / "simulation_output" / self.hostname
        root.mkdir(exist_ok=True, parents=True)
        return root / f"{self.hostname}_sys.log"

    def debug(self, msg: str):
        """
        Log a debug message.

        :param msg: The message to log.
        """
        self.logger.debug(msg)

    def info(self, msg: str):
        """
        Log an info message.

        :param msg: The message to log.
        """
        self.logger.info(msg)

    def warning(self, msg: str):
        """
        Log a warning message.

        :param msg: The message to log.
        """
        self.logger.warning(msg)

    def error(self, msg: str):
        """
        Log an error message.

        :param msg: The message to log.
        """
        self.logger.error(msg)

    def critical(self, msg: str):
        """
        Log a critical message.

        :param msg: The message to log.
        """
        self.logger.critical(msg)
