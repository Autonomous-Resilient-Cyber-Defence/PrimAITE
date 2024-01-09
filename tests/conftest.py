# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import pytest
import yaml

from primaite import getLogger
from primaite.game.game import PrimaiteGame
from primaite.session.session import PrimaiteSession

# from primaite.environment.primaite_env import Primaite
# from primaite.primaite_session import PrimaiteSession
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from tests.mock_and_patch.get_session_path_mock import temp_user_sessions_path

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1

_LOGGER = getLogger(__name__)

from primaite import PRIMAITE_PATHS

# PrimAITE v3 stuff
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.hardware.base import Link, Node


class TestService(Service):
    """Test Service class"""

    def __init__(self, **kwargs):
        kwargs["name"] = "TestService"
        kwargs["port"] = Port.HTTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        pass


class TestApplication(Application):
    """Test Application class"""

    def __init__(self, **kwargs):
        kwargs["name"] = "TestApplication"
        kwargs["port"] = Port.HTTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass


@pytest.fixture(scope="function")
def uc2_network() -> Network:
    return arcd_uc2_network()


@pytest.fixture(scope="function")
def service(file_system) -> TestService:
    return TestService(
        name="TestService", port=Port.ARP, file_system=file_system, sys_log=SysLog(hostname="test_service")
    )


@pytest.fixture(scope="function")
def service_class():
    return TestService


@pytest.fixture(scope="function")
def application(file_system) -> TestApplication:
    return TestApplication(
        name="TestApplication", port=Port.ARP, file_system=file_system, sys_log=SysLog(hostname="test_application")
    )


@pytest.fixture(scope="function")
def application_class():
    return TestApplication


@pytest.fixture(scope="function")
def file_system() -> FileSystem:
    return Node(hostname="fs_node").file_system


# PrimAITE v2 stuff
class TempPrimaiteSession(PrimaiteSession):
    """
    A temporary PrimaiteSession class.

    Uses context manager for deletion of files upon exit.
    """

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "TempPrimaiteSession":
        """Create a temporary PrimaiteSession object from a config file."""
        config_path = Path(config_path)
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return super().from_config(cfg=config)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass


@pytest.fixture
def temp_primaite_session(request, monkeypatch) -> TempPrimaiteSession:
    """Create a temporary PrimaiteSession object."""
    monkeypatch.setattr(PRIMAITE_PATHS, "user_sessions_path", temp_user_sessions_path())
    config_path = request.param[0]
    return TempPrimaiteSession.from_config(config_path=config_path)


@pytest.fixture(scope="function")
def client_server() -> Tuple[Computer, Server]:
    # Create Computer
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.0.1",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )

    # Create Server
    server = Server(
        hostname="server", ip_address="192.168.0.2", subnet_mask="255.255.255.0", operating_state=NodeOperatingState.ON
    )

    # Connect Computer and Server
    computer_nic = computer.nics[next(iter(computer.nics))]
    server_nic = server.nics[next(iter(server.nics))]
    link = Link(endpoint_a=computer_nic, endpoint_b=server_nic)

    # Should be linked
    assert link.is_up

    return computer, server


@pytest.fixture(scope="function")
def example_network() -> Network:
    """
    Create the network used for testing.

    Should only contain the nodes and links.
    This would act as the base network and services and applications are installed in the relevant test file,

    --------------                                                                          --------------
    |  client_1  |-----                                                                 ----|  server_1  |
    --------------    |     --------------      --------------      --------------     |    --------------
                      ------|  switch_2  |------|  router_1  |------|  switch_1  |------
    --------------    |     --------------      --------------      --------------     |   --------------
    |  client_2  |----                                                                 ----|  server_2  |
    --------------                                                                         --------------
    """
    network = Network()

    # Router 1
    router_1 = Router(hostname="router_1", num_ports=5, operating_state=NodeOperatingState.ON)
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.10.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=8, operating_state=NodeOperatingState.ON)
    network.connect(endpoint_a=router_1.ethernet_ports[1], endpoint_b=switch_1.switch_ports[8])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=8, operating_state=NodeOperatingState.ON)
    network.connect(endpoint_a=router_1.ethernet_ports[2], endpoint_b=switch_2.switch_ports[8])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        operating_state=NodeOperatingState.ON,
    )
    network.connect(endpoint_b=client_1.ethernet_port[1], endpoint_a=switch_2.switch_ports[1])

    # Client 2
    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.10.22",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        operating_state=NodeOperatingState.ON,
    )
    network.connect(endpoint_b=client_2.ethernet_port[1], endpoint_a=switch_2.switch_ports[2])

    # Domain Controller
    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )

    network.connect(endpoint_b=server_1.ethernet_port[1], endpoint_a=switch_1.switch_ports[1])

    # Database Server
    server_2 = Server(
        hostname="server_2",
        ip_address="192.168.1.14",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    network.connect(endpoint_b=server_2.ethernet_port[1], endpoint_a=switch_1.switch_ports[2])

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    return network
