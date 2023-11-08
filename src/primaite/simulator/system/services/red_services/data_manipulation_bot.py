from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.system.applications.database_client import DatabaseClient


class DataManipulationBot(DatabaseClient):
    """
    Red Agent Data Integration Service.

    The Service represents a bot that causes files/folders in the File System to
    become corrupted.
    """

    server_ip_address: Optional[IPv4Address] = None
    payload: Optional[str] = None
    server_password: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "DataManipulationBot"

    def configure(
        self, server_ip_address: IPv4Address, server_password: Optional[str] = None, payload: Optional[str] = None
    ):
        """
        Configure the DataManipulatorBot to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        :param payload: The data manipulation query payload.
        """
        self.server_ip_address = server_ip_address
        self.payload = payload
        self.server_password = server_password
        self.sys_log.info(
            f"{self.name}: Configured the {self.name} with {server_ip_address=}, {payload=}, {server_password=}."
        )

    def run(self):
        """Run the DataManipulationBot."""
        if self.server_ip_address and self.payload:
            self.sys_log.info(f"{self.name}: Attempting to start the {self.name}")
            super().run()
            if not self.connected:
                self.connect()
            if self.connected:
                self.query(self.payload)
                self.sys_log.info(f"{self.name} payload delivered: {self.payload}")
        else:
            self.sys_log.error(f"Failed to start the {self.name} as it requires both a target_ip_address and payload.")
