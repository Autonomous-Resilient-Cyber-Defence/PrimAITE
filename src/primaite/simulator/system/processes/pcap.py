import logging
from pathlib import Path


class _JSONFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter logs that start and end with '{' and '}' (JSON-like messages)."""
        return record.getMessage().startswith("{") and record.getMessage().endswith("}")


class PCAP:
    """
    A logger class for logging Frames as json strings.

    This is essentially a PrimAITE simulated version of PCAP.

    The PCAPs are logged to: <simulation output directory>/<hostname>/<hostname>_<ip address>_pcap.log
    """

    def __init__(self, hostname: str, ip_address: str):
        """
        Initialize the PCAP instance.

        :param hostname: The hostname for which PCAP logs are being recorded.
        :param ip_address: The IP address associated with the PCAP logs.
        """
        self.hostname = hostname
        self.ip_address = str(ip_address)
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger configuration."""
        log_path = self._get_log_path()

        file_handler = logging.FileHandler(filename=log_path)
        file_handler.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs

        log_format = "%(message)s"
        file_handler.setFormatter(logging.Formatter(log_format))

        logger_name = f"{self.hostname}_{self.ip_address}_pcap"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(60)  # Custom log level > CRITICAL to prevent any unwanted standard DEBUG-CRITICAL logs
        self.logger.addHandler(file_handler)

        self.logger.addFilter(_JSONFilter())

    def _get_log_path(self) -> Path:
        """Get the path for the log file."""
        root = Path(__file__).parent.parent.parent.parent.parent.parent / "simulation_output" / self.hostname
        root.mkdir(exist_ok=True, parents=True)
        return root / f"{self.hostname}_{self.ip_address}_pcap.log"

    def capture(self, frame):  # noqa Please don't make me, I'll have a circular import and cant use if TYPE_CHECKING ;(
        """
        Capture a Frame and log it.

        :param frame: The PCAP frame to capture.
        """
        msg = frame.model_dump_json()
        self.logger.log(level=60, msg=msg)  # Log at custom log level > CRITICAL
