from ipaddress import IPv4Address

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.red_services.data_manipulation_bot import DataManipulationBot


def test_creation():
    network = arcd_uc2_network()

    client_1: Node = network.get_node_by_hostname("client_1")

    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software["DataManipulationBot"]

    assert data_manipulation_bot.name == "DataManipulationBot"
    assert data_manipulation_bot.port == Port.POSTGRES_SERVER
    assert data_manipulation_bot.protocol == IPProtocol.TCP
    assert data_manipulation_bot.payload == "DELETE"
