# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Tuple

import pytest
from pydantic import Field

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


class BroadcastTestService(Service, discriminator="broadcast-test-service"):
    """A service for sending broadcast and unicast messages over a network."""

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for BroadcastTestService."""

        type: str = "broadcast-test-service"

    config: "BroadcastTestService.ConfigSchema" = Field(default_factory=lambda: BroadcastTestService.ConfigSchema())

    def __init__(self, **kwargs):
        # Set default service properties for broadcasting
        kwargs["name"] = "broadcast-test-service"
        kwargs["port"] = PORT_LOOKUP["HTTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        # Implement state description for the service
        pass

    def unicast(self, ip_address: IPv4Address):
        # Send a unicast payload to a specific IP address
        super().send(
            payload="unicast",
            dest_ip_address=ip_address,
            dest_port=PORT_LOOKUP["HTTP"],
        )

    def broadcast(self, ip_network: IPv4Network):
        # Send a broadcast payload to an entire IP network
        super().send(
            payload="broadcast", dest_ip_address=ip_network, dest_port=PORT_LOOKUP["HTTP"], ip_protocol=self.protocol
        )


class BroadcastTestClient(Application, discriminator="broadcast-test-client"):
    """A client application to receive broadcast and unicast messages."""

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for BroadcastTestClient."""

        type: str = "broadcast-test-client"

    config: ConfigSchema = Field(default_factory=lambda: BroadcastTestClient.ConfigSchema())

    payloads_received: List = []

    def __init__(self, **kwargs):
        # Set default client properties
        kwargs["name"] = "broadcast-test-client"
        kwargs["port"] = PORT_LOOKUP["HTTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        # Implement state description for the application
        pass

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        # Append received payloads to the list and print a message
        self.payloads_received.append(payload)
        print(f"Payload: {payload} received on node {self.sys_log.hostname}")


@pytest.fixture(scope="function")
def broadcast_network() -> Network:
    network = Network()

    client_1_cfg = {
        "type": "computer",
        "hostname": "client_1",
        "ip_address": "192.168.1.2",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.1.1",
        "start_up_duration": 0,
    }

    client_1: Computer = Computer.from_config(config=client_1_cfg)
    client_1.power_on()
    client_1.software_manager.install(BroadcastTestClient)
    application_1 = client_1.software_manager.software["broadcast-test-client"]
    application_1.run()
    client_2_cfg = {
        "type": "computer",
        "hostname": "client_2",
        "ip_address": "192.168.1.3",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.1.1",
        "start_up_duration": 0,
    }

    client_2: Computer = Computer.from_config(config=client_2_cfg)
    client_2.power_on()
    client_2.software_manager.install(BroadcastTestClient)
    application_2 = client_2.software_manager.software["broadcast-test-client"]
    application_2.run()

    server_1_cfg = {
        "type": "server",
        "hostname": "server_1",
        "ip_address": "192.168.1.1",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.1.1",
        "start_up_duration": 0,
    }

    server_1: Server = Server.from_config(config=server_1_cfg)

    server_1.power_on()

    server_1.software_manager.install(BroadcastTestService)
    service: BroadcastTestService = server_1.software_manager.software["broadcast-test-service"]
    service.start()

    switch_1: Switch = Switch.from_config(
        config={"type": "switch", "hostname": "switch_1", "num_ports": 6, "start_up_duration": 0}
    )
    switch_1.power_on()

    network.connect(endpoint_a=client_1.network_interface[1], endpoint_b=switch_1.network_interface[1])
    network.connect(endpoint_a=client_2.network_interface[1], endpoint_b=switch_1.network_interface[2])
    network.connect(endpoint_a=server_1.network_interface[1], endpoint_b=switch_1.network_interface[3])

    return network


@pytest.fixture(scope="function")
def broadcast_service_and_clients(
    broadcast_network,
) -> Tuple[BroadcastTestService, BroadcastTestClient, BroadcastTestClient]:
    client_1: BroadcastTestClient = broadcast_network.get_node_by_hostname("client_1").software_manager.software[
        "broadcast-test-client"
    ]
    client_2: BroadcastTestClient = broadcast_network.get_node_by_hostname("client_2").software_manager.software[
        "broadcast-test-client"
    ]
    service: BroadcastTestService = broadcast_network.get_node_by_hostname("server_1").software_manager.software[
        "broadcast-test-service"
    ]

    return service, client_1, client_2


def test_broadcast_correct_subnet(broadcast_service_and_clients):
    service, client_1, client_2 = broadcast_service_and_clients

    assert not client_1.payloads_received
    assert not client_2.payloads_received

    service.broadcast(IPv4Network("192.168.1.0/24"))

    assert client_1.payloads_received == ["broadcast"]
    assert client_2.payloads_received == ["broadcast"]


def test_broadcast_incorrect_subnet(broadcast_service_and_clients):
    service, client_1, client_2 = broadcast_service_and_clients

    assert not client_1.payloads_received
    assert not client_2.payloads_received

    service.broadcast(IPv4Network("192.168.2.0/24"))

    assert not client_1.payloads_received
    assert not client_2.payloads_received


def test_unicast_correct_address(broadcast_service_and_clients):
    service, client_1, client_2 = broadcast_service_and_clients

    assert not client_1.payloads_received
    assert not client_2.payloads_received

    service.unicast(IPv4Address("192.168.1.2"))

    assert client_1.payloads_received == ["unicast"]
    assert not client_2.payloads_received


def test_unicast_incorrect_address(broadcast_service_and_clients):
    service, client_1, client_2 = broadcast_service_and_clients

    assert not client_1.payloads_received
    assert not client_2.payloads_received

    service.unicast(IPv4Address("192.168.2.2"))

    assert not client_1.payloads_received
    assert not client_2.payloads_received
