# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.services.service import Service


class BroadcastTestService(Service):
    """A service for sending broadcast and unicast messages over a network."""

    def __init__(self, **kwargs):
        # Set default service properties for broadcasting
        kwargs["name"] = "BroadcastService"
        kwargs["port"] = Port.HTTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        # Implement state description for the service
        pass

    def unicast(self, ip_address: IPv4Address):
        # Send a unicast payload to a specific IP address
        super().send(
            payload="unicast",
            dest_ip_address=ip_address,
            dest_port=Port.HTTP,
        )

    def broadcast(self, ip_network: IPv4Network):
        # Send a broadcast payload to an entire IP network
        super().send(payload="broadcast", dest_ip_address=ip_network, dest_port=Port.HTTP, ip_protocol=self.protocol)


class BroadcastTestClient(Application, identifier="BroadcastTestClient"):
    """A client application to receive broadcast and unicast messages."""

    payloads_received: List = []

    def __init__(self, **kwargs):
        # Set default client properties
        kwargs["name"] = "BroadcastTestClient"
        kwargs["port"] = Port.HTTP
        kwargs["protocol"] = IPProtocol.TCP
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

    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    client_1.power_on()
    client_1.software_manager.install(BroadcastTestClient)
    application_1 = client_1.software_manager.software["BroadcastTestClient"]
    application_1.run()

    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    client_2.power_on()
    client_2.software_manager.install(BroadcastTestClient)
    application_2 = client_2.software_manager.software["BroadcastTestClient"]
    application_2.run()

    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_1.power_on()

    server_1.software_manager.install(BroadcastTestService)
    service: BroadcastTestService = server_1.software_manager.software["BroadcastService"]
    service.start()

    switch_1 = Switch(hostname="switch_1", num_ports=6, start_up_duration=0)
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
        "BroadcastTestClient"
    ]
    client_2: BroadcastTestClient = broadcast_network.get_node_by_hostname("client_2").software_manager.software[
        "BroadcastTestClient"
    ]
    service: BroadcastTestService = broadcast_network.get_node_by_hostname("server_1").software_manager.software[
        "BroadcastService"
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
