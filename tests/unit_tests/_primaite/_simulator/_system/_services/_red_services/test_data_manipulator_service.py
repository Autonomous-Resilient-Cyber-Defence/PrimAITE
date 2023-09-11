from ipaddress import IPv4Address

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.red_services.data_manipulator_service import DataManipulatorService


def test_creation():
    network = arcd_uc2_network()

    client_1: Node = network.get_node_by_hostname("client_1")

    client_1.software_manager.install(service_class=DataManipulatorService)

    data_manipulator_service: DataManipulatorService = client_1.software_manager.software["DataManipulatorBot"]

    assert data_manipulator_service.name == "DataManipulatorBot"
    assert data_manipulator_service.port == Port.POSTGRES_SERVER
    assert data_manipulator_service.protocol == IPProtocol.TCP

    # should have no session yet
    assert len(client_1.session_manager.sessions_by_uuid) == 0

    try:
        data_manipulator_service.start(target_ip_address=IPv4Address("192.168.1.14"))
    except Exception as e:
        assert False, f"Test was not supposed to throw exception: {e}"

    # there should be a session after the service is started
    assert len(client_1.session_manager.sessions_by_uuid) == 1
