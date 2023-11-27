import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from primaite.simulator import SIM_OUTPUT


class _JSONFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter logs that start and end with '{' and '}' (JSON-like messages)."""
        return record.getMessage().startswith("{") and record.getMessage().endswith("}")


class PacketCapture:
    """
    Represents a PacketCapture component on a Node in the simulation environment.

    PacketCapture is a service that logs Frames as json strings; It's Wireshark for PrimAITE.

    The PCAPs are logged to: <simulation output directory>/<hostname>/<hostname>_<ip address>_pcap.log
    """

    def __init__(self, hostname: str, ip_address: Optional[str] = None, switch_port_number: Optional[int] = None):
        """
        Initialize the PacketCapture process.

        :param hostname: The hostname for which PCAP logs are being recorded.
        :param ip_address: The IP address associated with the PCAP logs.
        """
        self.hostname: str = hostname
        "The hostname for which PCAP logs are being recorded."
        self.ip_address: str = ip_address
        "The IP address associated with the PCAP logs."
        self.switch_port_number = switch_port_number
        "The SwitchPort number."

        self.current_episode: int = 1

        self.setup_logger()

    def setup_logger(self):
        """Set up the logger configuration."""
        log_path = self._get_log_path()

        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs

        log_format = "%(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        self.logger = logging.getLogger(self._logger_name)
        self.logger.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs
        self.logger.addHandler(file_handler)

        self.logger.addFilter(_JSONFilter())

    def read(self) -> List[Dict[str, Any]]:
        """
        Read packet capture logs and return them as a list of dictionaries.

        :return: List of frames captured, represented as dictionaries.
        """
        frames = []
        with open(self._get_log_path(), "r") as file:
            while line := file.readline():
                frames.append(json.loads(line.rstrip()))
        return frames

    @property
    def _logger_name(self) -> str:
        """Get PCAP the logger name."""
        if self.ip_address:
            return f"{self.hostname}_{self.ip_address}_pcap"
        if self.switch_port_number:
            return f"{self.hostname}_port-{self.switch_port_number}_pcap"
        return f"{self.hostname}_pcap"

    def _get_log_path(self) -> Path:
        """Get the path for the log file."""
        root = SIM_OUTPUT.path / f"episode_{self.current_episode}" / self.hostname
        root.mkdir(exist_ok=True, parents=True)
        return root / f"{self._logger_name}.log"

    def capture(self, frame):  # noqa - I'll have a circular import and cant use if TYPE_CHECKING ;(
        """
        Capture a Frame and log it.

        :param frame: The PCAP frame to capture.
        """
        msg = frame.model_dump_json()
        self.logger.log(level=60, msg=msg)  # Log at custom log level > CRITICAL
