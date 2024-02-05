import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.protocols.http import (
    HttpRequestMethod,
    HttpRequestPacket,
    HttpResponsePacket,
    HttpStatusCode,
)
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def web_server() -> Server:
    node = Server(
        hostname="web_server",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    node.software_manager.install(software_class=WebServer)
    node.software_manager.software.get("WebServer").start()
    return node


def test_create_web_server(web_server):
    assert web_server is not None
    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")
    assert web_server_service.name is "WebServer"
    assert web_server_service.port is Port.HTTP
    assert web_server_service.protocol is IPProtocol.TCP


def test_handling_get_request_not_found_path(web_server):
    payload = HttpRequestPacket(request_method=HttpRequestMethod.GET, request_url="http://domain.com/fake-path")

    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")

    response: HttpResponsePacket = web_server_service._handle_get_request(payload=payload)
    assert response.status_code == HttpStatusCode.NOT_FOUND


def test_handling_get_request_home_page(web_server):
    payload = HttpRequestPacket(request_method=HttpRequestMethod.GET, request_url="http://domain.com/")

    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")

    response: HttpResponsePacket = web_server_service._handle_get_request(payload=payload)
    assert response.status_code == HttpStatusCode.OK


def test_process_http_request_get(web_server):
    payload = HttpRequestPacket(request_method=HttpRequestMethod.GET, request_url="http://domain.com/")

    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")

    assert web_server_service._process_http_request(payload=payload) is True


def test_process_http_request_method_not_allowed(web_server):
    payload = HttpRequestPacket(request_method=HttpRequestMethod.DELETE, request_url="http://domain.com/")

    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")

    assert web_server_service._process_http_request(payload=payload) is False
