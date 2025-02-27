# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import logging
from pathlib import Path

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator import LogLevel, SIM_OUTPUT


class _NotJSONFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determines if a log message does not start and end with '{' and '}' (i.e., it is not a JSON-like message).

        :param record: LogRecord object containing all the information pertinent to the event being logged.
        :return: True if log message is not JSON-like, False otherwise.
        """
        return not record.getMessage().startswith("{") and not record.getMessage().endswith("}")


class SysLog:
    """
    A SysLog class is a simple logger dedicated to managing and writing system logs for a Node.

    Each log message is written to a file located at: <simulation output directory>/<hostname>/<hostname>_sys.log
    """

    def __init__(self, hostname: str):
        """
        Constructs a SysLog instance for a given hostname.

        :param hostname: The hostname associated with the system logs being recorded.
        """
        self.hostname = hostname
        self.current_episode: int = 1
        self.setup_logger()

    def setup_logger(self):
        """
        Configures the logger for this SysLog instance.

        The logger is set to the DEBUG level, and is equipped with a handler that writes to a file and filters out
        JSON-like messages.
        """
        if not SIM_OUTPUT.save_sys_logs:
            return

        log_path = self._get_log_path()
        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(logging.DEBUG)

        log_format = "%(asctime)s::%(levelname)s::%(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        self.logger = logging.getLogger(f"{self.hostname}_sys_log")
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        self.logger.addFilter(_NotJSONFilter())

    def show(self, last_n: int = 10, markdown: bool = False):
        """
        Print the Node Sys Log as a table.

        Generate and print PrettyTable instance that shows the Nodes Sys Log, with columns Timestamp, Level,
        and Massage.

        :param markdown: Use Markdown style in table output. Defaults to False.
        """
        table = PrettyTable(["Timestamp", "Level", "Message"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Sys Log"
        if self._get_log_path().exists():
            with open(self._get_log_path()) as file:
                lines = file.readlines()
            for line in lines[-last_n:]:
                table.add_row(line.strip().split("::"))
        print(table)

    def _get_log_path(self) -> Path:
        """
        Constructs the path for the log file based on the hostname.

        :return: Path object representing the location of the log file.
        """
        root = SIM_OUTPUT.path / f"episode_{self.current_episode}" / self.hostname
        root.mkdir(exist_ok=True, parents=True)
        return root / f"{self.hostname}_sys.log"

    def _write_to_terminal(self, msg: str, level: str, to_terminal: bool = False):
        if to_terminal or SIM_OUTPUT.write_sys_log_to_terminal:
            print(f"{self.hostname}: ({level}) {msg}")

    def debug(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the DEBUG level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.sys_log_level > LogLevel.DEBUG:
            return

        if SIM_OUTPUT.save_sys_logs:
            self.logger.debug(msg)
        self._write_to_terminal(msg, "DEBUG", to_terminal)

    def info(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the INFO level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.sys_log_level > LogLevel.INFO:
            return

        if SIM_OUTPUT.save_sys_logs:
            self.logger.info(msg)
        self._write_to_terminal(msg, "INFO", to_terminal)

    def warning(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the WARNING level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.sys_log_level > LogLevel.WARNING:
            return

        if SIM_OUTPUT.save_sys_logs:
            self.logger.warning(msg)
        self._write_to_terminal(msg, "WARNING", to_terminal)

    def error(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the ERROR level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.sys_log_level > LogLevel.ERROR:
            return

        if SIM_OUTPUT.save_sys_logs:
            self.logger.error(msg)
        self._write_to_terminal(msg, "ERROR", to_terminal)

    def critical(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the CRITICAL level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if LogLevel.CRITICAL < SIM_OUTPUT.sys_log_level:
            return

        if SIM_OUTPUT.save_sys_logs:
            self.logger.critical(msg)
        self._write_to_terminal(msg, "CRITICAL", to_terminal)
