from typing import Tuple

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.protocols.http import HttpStatusCode
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def web_client_and_web_server(client_server) -> Tuple[WebBrowser, Computer, WebServer, Server]:
    computer, server = client_server

    # Install Web Browser on computer
    computer.software_manager.install(WebBrowser)
    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    web_browser.run()

    # Install DNS Client service on computer
    computer.software_manager.install(DNSClient)
    dns_client: DNSClient = computer.software_manager.software.get("DNSClient")
    # set dns server
    dns_client.dns_server = server.network_interfaces[next(iter(server.network_interfaces))].ip_address

    # Install Web Server service on server
    server.software_manager.install(WebServer)
    web_server_service: WebServer = server.software_manager.software.get("WebServer")
    web_server_service.start()

    # Install DNS Server service on server
    server.software_manager.install(DNSServer)
    dns_server: DNSServer = server.software_manager.software.get("DNSServer")
    # register arcd.com to DNS
    dns_server.dns_register(domain_name="arcd.com", domain_ip_address=server.network_interfaces[next(iter(server.network_interfaces))].ip_address)

    return web_browser, computer, web_server_service, server


def test_web_page_get_users_page_request_with_domain_name(web_client_and_web_server):
    """Test to see if the client can handle requests with domain names"""
    web_browser_app, computer, web_server_service, server = web_client_and_web_server

    web_server_ip = server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address
    web_browser_app.target_url = f"http://arcd.com/"
    assert web_browser_app.operating_state == ApplicationOperatingState.RUNNING

    assert web_browser_app.get_webpage() is True

    # latest response should have status code 200
    assert web_browser_app.latest_response is not None
    assert web_browser_app.latest_response.status_code == HttpStatusCode.OK


def test_web_page_get_users_page_request_with_ip_address(web_client_and_web_server):
    """Test to see if the client can handle requests that use ip_address."""
    web_browser_app, computer, web_server_service, server = web_client_and_web_server

    web_server_ip = server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address
    web_browser_app.target_url = f"http://{web_server_ip}/"
    assert web_browser_app.operating_state == ApplicationOperatingState.RUNNING

    assert web_browser_app.get_webpage() is True

    # latest response should have status code 200
    assert web_browser_app.latest_response is not None
    assert web_browser_app.latest_response.status_code == HttpStatusCode.OK


def test_web_page_request_from_shut_down_server(web_client_and_web_server):
    """Test to see that the web server does not respond when the server is off."""
    web_browser_app, computer, web_server_service, server = web_client_and_web_server

    web_server_ip = server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address
    web_browser_app.target_url = f"http://arcd.com/"
    assert web_browser_app.operating_state == ApplicationOperatingState.RUNNING

    assert web_browser_app.get_webpage() is True

    # latest response should have status code 200
    assert web_browser_app.latest_response is not None
    assert web_browser_app.latest_response.status_code == HttpStatusCode.OK

    server.power_off()

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    # node should be off
    assert server.operating_state is NodeOperatingState.OFF

    assert web_browser_app.get_webpage() is False
    assert web_browser_app.latest_response.status_code == HttpStatusCode.NOT_FOUND


def test_web_page_request_from_closed_web_browser(web_client_and_web_server):
    web_browser_app, computer, web_server_service, server = web_client_and_web_server

    assert web_browser_app.operating_state == ApplicationOperatingState.RUNNING
    web_browser_app.target_url = f"http://arcd.com/"
    assert web_browser_app.get_webpage() is True

    # latest response should have status code 200
    assert web_browser_app.latest_response.status_code == HttpStatusCode.OK

    web_browser_app.close()

    # node should be off
    assert web_browser_app.operating_state is ApplicationOperatingState.CLOSED

    assert web_browser_app.get_webpage() is False
