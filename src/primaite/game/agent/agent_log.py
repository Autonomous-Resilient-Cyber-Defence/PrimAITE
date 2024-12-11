# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import logging
from pathlib import Path
from typing import Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel

from primaite.simulator import LogLevel, SIM_OUTPUT


class _NotJSONFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determines if a log message does not start and end with '{' and '}' (i.e., it is not a JSON-like message).

        :param record: LogRecord object containing all the information pertinent to the event being logged.
        :return: True if log message is not JSON-like, False otherwise.
        """
        return not record.getMessage().startswith("{") and not record.getMessage().endswith("}")


class AgentLog(BaseModel):
    """
    A Agent Log class is a simple logger dedicated to managing and writing logging updates and information for an agent.

    Each log message is written to a file located at: <simulation output directory>/agent_name/agent_name.log
    """

    agent_name: str = "unnamed_agent"
    current_episode: int = 1
    current_timestep: int = 0

    def __init__(self, agent_name: Optional[str]):
        """
        Constructs a Agent Log instance for a given hostname.

        :param hostname: The hostname associated with the system logs being recorded.
        """
        super().__init__()
        self.agent_name = agent_name or "unnamed_agent"
        # self.current_episode: int = 1
        # self.current_timestep: int = 0
        self.setup_logger()

    @property
    def timestep(self) -> int:
        """Returns the current timestep. Used for log indexing.

        :return: The current timestep as an Int.
        """
        return self.current_timestep

    def update_timestep(self, new_timestep: int):
        """
        Updates the self.current_timestep attribute with the given parameter.

        This method is called within .step() to ensure that all instances of Agent Logs
        are in sync with one another.

        :param new_timestep: The new timestep.
        """
        self.current_timestep = new_timestep

    def setup_logger(self):
        """
        Configures the logger for this Agent Log instance.

        The logger is set to the DEBUG level, and is equipped with a handler that writes to a file and filters out
        JSON-like messages.
        """
        if not SIM_OUTPUT.save_agent_logs:
            return

        log_path = self._get_log_path()
        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(logging.DEBUG)

        log_format = "%(timestep)s::%(levelname)s::%(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        self.logger = logging.getLogger(f"{self.agent_name}_log")
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def _get_log_path(self) -> Path:
        """
        Constructs the path for the log file based on the agent name.

        :return: Path object representing the location of the log file.
        """
        root = SIM_OUTPUT.agent_behaviour_path / f"episode_{self.current_episode}" / self.agent_name
        root.mkdir(exist_ok=True, parents=True)
        return root / f"{self.agent_name}.log"

    def _write_to_terminal(self, msg: str, level: str, to_terminal: bool = False):
        if to_terminal or SIM_OUTPUT.write_agent_log_to_terminal:
            print(f"{self.agent_name}: ({ self.timestep}) ({level}) {msg}")

    def debug(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the DEBUG level.

        :param msg: The message to be logged.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.agent_log_level > LogLevel.DEBUG:
            return

        if SIM_OUTPUT.save_agent_logs:
            self.logger.debug(msg, extra={"timestep": self.timestep})
        self._write_to_terminal(msg, "DEBUG", to_terminal)

    def info(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the INFO level.

        :param msg: The message to be logged.
        :param timestep: The current timestep.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.agent_log_level > LogLevel.INFO:
            return

        if SIM_OUTPUT.save_agent_logs:
            self.logger.info(msg, extra={"timestep": self.timestep})
        self._write_to_terminal(msg, "INFO", to_terminal)

    def warning(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the WARNING level.

        :param msg: The message to be logged.
        :param timestep: The current timestep.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.agent_log_level > LogLevel.WARNING:
            return

        if SIM_OUTPUT.save_agent_logs:
            self.logger.warning(msg, extra={"timestep": self.timestep})
        self._write_to_terminal(msg, "WARNING", to_terminal)

    def error(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the ERROR level.

        :param msg: The message to be logged.
        :param timestep: The current timestep.
        :param to_terminal: If True, prints to the terminal too.
        """
        if SIM_OUTPUT.agent_log_level > LogLevel.ERROR:
            return

        if SIM_OUTPUT.save_agent_logs:
            self.logger.error(msg, extra={"timestep": self.timestep})
        self._write_to_terminal(msg, "ERROR", to_terminal)

    def critical(self, msg: str, to_terminal: bool = False):
        """
        Logs a message with the CRITICAL level.

        :param msg: The message to be logged.
        :param timestep: The current timestep.
        :param to_terminal: If True, prints to the terminal too.
        """
        if LogLevel.CRITICAL < SIM_OUTPUT.agent_log_level:
            return

        if SIM_OUTPUT.save_agent_logs:
            self.logger.critical(msg, extra={"timestep": self.timestep})
        self._write_to_terminal(msg, "CRITICAL", to_terminal)

    def show(self, last_n: int = 10, markdown: bool = False):
        """
        Print an Agents Log as a table.

        Generate and print PrettyTable instance that shows the agents behaviour log, with columns Time step,
        Level and Message.

        :param markdown: Use Markdown style in table output. Defaults to False.
        """
        table = PrettyTable(["Time Step", "Level", "Message"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.agent_name} Behaviour Log"
        if self._get_log_path().exists():
            with open(self._get_log_path()) as file:
                lines = file.readlines()
            for line in lines[-last_n:]:
                table.add_row(line.strip().split("::"))
        print(table)
