import logging
from pathlib import Path
from typing import Optional

from primaite.simulator import TEMP_SIM_OUTPUT


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

    def __init__(self, hostname: str, ip_address: Optional[str] = None):
        """
        Initialize the PacketCapture process.

        :param hostname: The hostname for which PCAP logs are being recorded.
        :param ip_address: The IP address associated with the PCAP logs.
        """
        self.hostname: str = hostname
        "The hostname for which PCAP logs are being recorded."
        self.ip_address: str = ip_address
        "The IP address associated with the PCAP logs."
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger configuration."""
        log_path = self._get_log_path()

        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs

        log_format = "%(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        logger_name = f"{self.hostname}_{self.ip_address}_pcap" if self.ip_address else f"{self.hostname}_pcap"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs
        self.logger.addHandler(file_handler)

        self.logger.addFilter(_JSONFilter())

    def _get_log_path(self) -> Path:
        """Get the path for the log file."""
        root = TEMP_SIM_OUTPUT / self.hostname
        root.mkdir(exist_ok=True, parents=True)
        if self.ip_address:
            return root / f"{self.hostname}_{self.ip_address}_pcap.log"
        return root / f"{self.hostname}_pcap.log"

    def capture(self, frame):  # noqa - I'll have a circular import and cant use if TYPE_CHECKING ;(
        """
        Capture a Frame and log it.

        :param frame: The PCAP frame to capture.
        """
        msg = frame.model_dump_json()
        self.logger.log(level=60, msg=msg)  # Log at custom log level > CRITICAL
