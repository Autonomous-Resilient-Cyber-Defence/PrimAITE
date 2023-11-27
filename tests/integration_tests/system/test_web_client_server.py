from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.http import HttpStatusCode
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser


def test_web_page_home_page(uc2_network):
    """Test to see if the browser is able to open the main page of the web server."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()
    web_client.target_url = "http://arcd.com/"
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage() is True

    # latest reponse should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HttpStatusCode.OK


def test_web_page_get_users_page_request_with_domain_name(uc2_network):
    """Test to see if the client can handle requests with domain names"""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage() is True

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
    web_client.target_url = f"http://{web_server_ip}/users/"
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage() is True

    # latest reponse should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HttpStatusCode.OK
