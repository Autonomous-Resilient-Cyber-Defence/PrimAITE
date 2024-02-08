# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import pytest
import yaml

from primaite import getLogger, PRIMAITE_PATHS
from primaite.session.session import PrimaiteSession
from primaite.simulator.file_system.file_system import FileSystem

# from primaite.environment.primaite_env import Primaite
# from primaite.primaite_session import PrimaiteSession
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
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


class TestService(Service):
    """Test Service class"""

    def describe_state(self) -> Dict:
        return super().describe_state()

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
        return super().describe_state()


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
    return Computer(hostname="fs_node", ip_address="192.168.1.2", subnet_mask="255.255.255.0").file_system


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
    network = Network()

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Connect Computer and Server
    network.connect(computer.network_interface[1], server.network_interface[1])

    # Should be linked
    assert next(iter(network.links.values())).is_up

    return computer, server


@pytest.fixture(scope="function")
def client_switch_server() -> Tuple[Computer, Switch, Server]:
    network = Network()

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    switch = Switch(hostname="switch", start_up_duration=0)
    switch.power_on()

    network.connect(endpoint_a=computer.network_interface[1], endpoint_b=switch.network_interface[1])
    network.connect(endpoint_a=server.network_interface[1], endpoint_b=switch.network_interface[2])

    assert all(link.is_up for link in network.links.values())

    return computer, switch, server


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
    router_1 = Router(hostname="router_1", start_up_duration=0)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.10.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=8, start_up_duration=0)
    switch_1.power_on()

    network.connect(endpoint_a=router_1.network_interface[1], endpoint_b=switch_1.network_interface[8])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=8, start_up_duration=0)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.network_interface[2], endpoint_b=switch_2.network_interface[8])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        start_up_duration=0,
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])

    # Client 2
    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.10.22",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        start_up_duration=0,
    )
    client_2.power_on()
    network.connect(endpoint_b=client_2.network_interface[1], endpoint_a=switch_2.network_interface[2])

    # Server 1
    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_1.power_on()
    network.connect(endpoint_b=server_1.network_interface[1], endpoint_a=switch_1.network_interface[1])

    # DServer 2
    server_2 = Server(
        hostname="server_2",
        ip_address="192.168.1.14",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_2.power_on()
    network.connect(endpoint_b=server_2.network_interface[1], endpoint_a=switch_1.network_interface[2])

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    assert all(link.is_up for link in network.links.values())

    return network
