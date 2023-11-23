from typing import Tuple

import pytest
from conftest import TestService

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.services.service import Service, ServiceOperatingState


@pytest.fixture(scope="function")
def service_on_node() -> Tuple[Server, Service]:
    server = Server(
        hostname="server", ip_address="192.168.0.1", subnet_mask="255.255.255.0", operating_state=NodeOperatingState.ON
    )
    server.software_manager.install(TestService)

    service = server.software_manager.software["TestService"]
    service.start()

    return server, service


def test_server_turns_off_service(service_on_node):
    """Check that the service is turned off when the server is turned off"""
    server, service = service_on_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED


def test_server_turns_on_service(service_on_node):
    """Check that turning on the server turns on service."""
    pass
