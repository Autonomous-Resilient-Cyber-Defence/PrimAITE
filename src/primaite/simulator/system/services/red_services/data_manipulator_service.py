from ipaddress import IPv4Address

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service


class DataManipulatorService(Service):
    """
    Red Agent Data Integration Service.

    The Service represents a bot that causes files/folders in the File System to
    become corrupted.
    """

    def __init__(self, **kwargs):
        kwargs["name"] = "DataManipulatorBot"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def run(self):
        """Run the DataManipulatorService actions."""
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload="SELECT * FROM users", dest_ip_address=IPv4Address("192.168.1.14"), dest_port=self.port
        )
