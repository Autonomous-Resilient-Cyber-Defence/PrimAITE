import pytest

from src.primaite.simulator.network.hardware.nodes.computer import Computer
from src.primaite.simulator.network.protocols.http import HttpResponsePacket, HttpStatusCode
from src.primaite.simulator.network.transmission.network_layer import IPProtocol
from src.primaite.simulator.network.transmission.transport_layer import Port
from src.primaite.simulator.system.applications.web_browser import WebBrowser


@pytest.fixture(scope="function")
def web_client() -> Computer:
    node = Computer(
        hostname="web_client", ip_address="192.168.1.11", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    return node


def test_create_web_client(web_client):
    assert web_client is not None
    web_browser: WebBrowser = web_client.software_manager.software["WebBrowser"]
    assert web_browser.name is "WebBrowser"
    assert web_browser.port is Port.HTTP
    assert web_browser.protocol is IPProtocol.TCP


def test_receive_invalid_payload(web_client):
    web_browser: WebBrowser = web_client.software_manager.software["WebBrowser"]

    assert web_browser.receive(payload={}) is False


def test_receive_payload(web_client):
    payload = HttpResponsePacket(status_code=HttpStatusCode.OK)
    web_browser: WebBrowser = web_client.software_manager.software["WebBrowser"]
    assert web_browser.latest_response is None

    web_browser.receive(payload=payload)

    assert web_browser.latest_response is not None
