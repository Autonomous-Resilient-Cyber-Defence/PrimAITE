import pytest

from primaite.simulator.network.hardware.base import Node, NodeOperatingState
from primaite.simulator.system.processes.process import Process
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture
def node() -> Node:
    return Node(hostname="test")


def test_node_startup(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    assert node.operating_state == NodeOperatingState.BOOTING

    idx = 0
    while node.operating_state == NodeOperatingState.BOOTING:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.ON


def test_node_shutdown(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    idx = 0
    while node.operating_state == NodeOperatingState.BOOTING:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.ON

    node.apply_request(["shutdown"])

    idx = 0
    while node.operating_state == NodeOperatingState.SHUTTING_DOWN:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.OFF


def test_node_os_scan(node):
    """Test OS Scanning."""
    # add process to node
    node.processes["process"] = Process(name="process")
    node.processes["process"].health_state_actual = SoftwareHealthState.COMPROMISED
    assert node.processes["process"].health_state_visible == SoftwareHealthState.GOOD

    # add services to node
    service = Service(name="service")
    service.health_state_actual = SoftwareHealthState.COMPROMISED
    node.install_service(service=service)

    # add application to node

    # add file to node

    # run os scan
    node.apply_request(["os", "scan"])

    # apply time steps
    for i in range(20):
        node.apply_timestep(timestep=i)

    # should update the state of all items
    assert node.processes["process"].health_state_visible == SoftwareHealthState.COMPROMISED
    assert service.health_state_visible == SoftwareHealthState.COMPROMISED
