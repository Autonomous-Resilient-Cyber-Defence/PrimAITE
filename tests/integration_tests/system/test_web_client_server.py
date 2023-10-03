from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.protocols.http import HTTPStatusCode
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.service import ServiceOperatingState


def test_web_page_get_request(uc2_network):
    """Test to see if the client retrieves the correct web files."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    web_client: WebBrowser = client_1.software_manager.software["WebBrowser"]
    web_client.run()
    assert web_client.operating_state == ApplicationOperatingState.RUNNING

    assert web_client.get_webpage("http://arcd.com/index.html") is True

    # latest reponse should have status code 200
    assert web_client.latest_response is not None
    assert web_client.latest_response.status_code == HTTPStatusCode.OK
