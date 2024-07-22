import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.protocols.http import HttpResponsePacket, HttpStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser


@pytest.fixture(scope="function")
def web_browser() -> WebBrowser:
    computer = Computer(
        hostname="web_client",
        ip_address="192.168.1.11",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()
    # Web Browser should be pre-installed in computer
    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    web_browser.run()
    assert web_browser.operating_state is ApplicationOperatingState.RUNNING
    return web_browser


def test_create_web_client():
    computer = Computer(
        hostname="web_client",
        ip_address="192.168.1.11",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()
    # Web Browser should be pre-installed in computer
    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    assert web_browser.name is "WebBrowser"
    assert web_browser.port is Port.HTTP
    assert web_browser.protocol is IPProtocol.TCP


def test_receive_invalid_payload(web_browser):
    assert web_browser.receive(payload={}) is False


def test_receive_payload(web_browser):
    payload = HttpResponsePacket(status_code=HttpStatusCode.OK)
    assert web_browser.latest_response is None

    web_browser.receive(payload=payload)

    assert web_browser.latest_response is not None


def test_invalid_target_url(web_browser):
    # none value target url
    web_browser.target_url = None
    assert web_browser.get_webpage() is False


def test_non_existent_target_url(web_browser):
    web_browser.target_url = "http://192.168.255.255"
    assert web_browser.get_webpage() is False
