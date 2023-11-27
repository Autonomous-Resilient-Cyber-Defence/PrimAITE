from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.http import HttpStatusCode
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.service import ServiceOperatingState


def test_web_page_home_page(uc2_network):
    """Test to see if the browser is able to open the main page of the web server."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage("http://arcd.com/") is True

    # latest reponse should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HttpStatusCode.OK


def test_web_page_get_users_page_request_with_domain_name(uc2_network):
    """Test to see if the client can handle requests with domain names"""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage("http://arcd.com/users/") is True

    # latest reponse should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HttpStatusCode.OK


def test_web_page_get_users_page_request_with_ip_address(uc2_network):
    """Test to see if the client can handle requests that use ip_address."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    web_server_ip = web_server.nics.get(next(iter(web_server.nics))).ip_address

    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage(f"http://{web_server_ip}/users/") is True

    # latest response should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HttpStatusCode.OK


def test_web_page_request_from_shut_down_server(uc2_network):
    """Test to see that the web server does not respond when the server is off."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()

    web_server: Server = uc2_network.get_node_by_hostname("web_server")

    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage("http://arcd.com/users/") is True

    # latest response should have status code 200
    assert web_client.latest_response.status_code == HttpStatusCode.OK

    web_server.power_off()

    for i in range(web_server.shut_down_duration + 1):
        uc2_network.apply_timestep(timestep=i)

    # node should be off
    assert web_server.operating_state is NodeOperatingState.OFF

    assert web_client.get_webpage("http://arcd.com/users/") is False
    assert web_client.latest_response.status_code == HttpStatusCode.NOT_FOUND


def test_web_page_request_from_closed_web_browser(uc2_network):
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()

    web_server: Server = uc2_network.get_node_by_hostname("web_server")

    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage("http://arcd.com/users/") is True

    # latest response should have status code 200
    assert web_client.latest_response.status_code == HttpStatusCode.OK

    web_client.close()

    # node should be off
    assert web_client.operating_state is ApplicationOperatingState.CLOSED

    assert web_client.get_webpage("http://arcd.com/users/") is False
