from typing import Tuple

import pytest
from conftest import TestApplication, TestService

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState
from primaite.simulator.system.services.service import Service, ServiceOperatingState


@pytest.fixture(scope="function")
def populated_node() -> Tuple[Application, Server, Service]:
    server = Server(
        hostname="server", ip_address="192.168.0.1", subnet_mask="255.255.255.0", operating_state=NodeOperatingState.ON
    )
    server.software_manager.install(TestService)
    server.software_manager.install(TestApplication)

    app = server.software_manager.software["TestApplication"]
    app.run()
    service = server.software_manager.software["TestService"]
    service.start()

    return app, server, service


def test_server_turns_off_service(populated_node):
    """Check that the service is turned off when the server is turned off"""
    app, server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING
    assert app.operating_state is ApplicationOperatingState.RUNNING

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_service_cannot_be_turned_on_when_server_is_off(populated_node):
    """Check that the service cannot be started when the server is off."""
    app, server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING
    assert app.operating_state is ApplicationOperatingState.RUNNING

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED
    assert app.operating_state is ApplicationOperatingState.CLOSED

    service.start()
    app.run()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_server_turns_on_service(populated_node):
    """Check that turning on the server turns on service."""
    app, server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING
    assert app.operating_state is ApplicationOperatingState.RUNNING

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED
    assert app.operating_state is ApplicationOperatingState.CLOSED

    server.power_on()

    for i in range(server.start_up_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING
    assert app.operating_state is ApplicationOperatingState.RUNNING
