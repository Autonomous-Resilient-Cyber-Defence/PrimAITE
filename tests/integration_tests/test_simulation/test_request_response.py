# some test cases:
# 0. test that sending a request to a valid target results in a success
# 1. test that sending a request to a component that doesn't exist results in a failure
# 2. test that sending a request to a software on a turned-off component results in a failure
# 3. test every implemented action under several different situation, some of which should lead to a success and some to a failure.

import pytest

from primaite.interface.request import RequestResponse
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.host_node import HostNode
from tests.conftest import TestApplication, TestService


def test_successful_application_requests(example_network):
    net = example_network

    client_1 = net.get_node_by_hostname("client_1")
    client_1.software_manager.install(TestApplication)
    client_1.software_manager.software.get("TestApplication").run()

    resp_1 = net.apply_request(["node", "client_1", "application", "TestApplication", "scan"])
    assert resp_1 == RequestResponse(status="success", data={})
    resp_2 = net.apply_request(["node", "client_1", "application", "TestApplication", "patch"])
    assert resp_2 == RequestResponse(status="success", data={})
    resp_3 = net.apply_request(["node", "client_1", "application", "TestApplication", "compromise"])
    assert resp_3 == RequestResponse(status="success", data={})


def test_successful_service_requests(example_network):
    net = example_network
    server_1 = net.get_node_by_hostname("server_1")
    server_1.software_manager.install(TestService)

    # Careful: the order here is important, for example we cannot run "stop" unless we run "start" first
    for verb in [
        "disable",
        "enable",
        "start",
        "stop",
        "start",
        "restart",
        "pause",
        "resume",
        "compromise",
        "scan",
        "patch",
    ]:
        resp_1 = net.apply_request(["node", "server_1", "service", "TestService", verb])
        assert resp_1 == RequestResponse(status="success", data={})
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        server_1.apply_timestep(timestep=1)
        # lazily apply timestep 7 times to make absolutely sure any time-based things like restart have a chance to finish


def test_non_existent_requests(example_network):
    net = example_network
    resp_1 = net.apply_request(["fake"])
    assert resp_1.status == "unreachable"
    resp_2 = net.apply_request(["network", "node", "client_39", "application", "WebBrowser", "execute"])
    assert resp_2.status == "unreachable"


@pytest.mark.parametrize(
    "node_request",
    [
        ["node", "client_1", "file_system", "folder", "root", "scan"],
        ["node", "client_1", "os", "scan"],
        ["node", "client_1", "service", "DNSClient", "stop"],
        ["node", "client_1", "application", "WebBrowser", "scan"],
        ["node", "client_1", "network_interface", 1, "disable"],
    ],
)
def test_request_fails_if_node_off(example_network, node_request):
    """Test that requests succeed when the node is on, and fail if the node is off."""
    net = example_network
    client_1: HostNode = net.get_node_by_hostname("client_1")
    client_1.shut_down_duration = 0

    assert client_1.operating_state == NodeOperatingState.ON
    resp_1 = net.apply_request(node_request)
    assert resp_1.status == "success"

    client_1.power_off()
    assert client_1.operating_state == NodeOperatingState.OFF
    resp_2 = net.apply_request(node_request)
    assert resp_2.status == "failure"
