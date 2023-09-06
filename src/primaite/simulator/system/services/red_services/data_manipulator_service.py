from ipaddress import IPv4Address
from typing import Any, Optional

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
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

    def start(self, target_ip_address: IPv4Address, payload: Optional[Any] = "DELETE TABLE users", **kwargs):
        """
        Run the DataManipulatorService actions.

        :param: target_ip_address: The IP address of the target machine to attack
        :param: payload: The payload to send to the target machine
        """
        super().start()

        self.software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=target_ip_address, dest_port=self.port
        )
