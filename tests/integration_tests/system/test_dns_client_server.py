from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.service import ServiceOperatingState


def test_dns_client_server(uc2_network):
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    domain_controller: Server = uc2_network.get_node_by_hostname("domain_controller")

    dns_client: DNSClient = client_1.software_manager.software["DNSClient"]
    dns_server: DNSServer = domain_controller.software_manager.software["DNSServer"]

    assert dns_client.operating_state == ServiceOperatingState.RUNNING
    assert dns_server.operating_state == ServiceOperatingState.RUNNING

    dns_server.show()

    # fake domain should not be added to dns cache
    assert not dns_client.check_domain_exists(target_domain="fake-domain.com")
    assert dns_client.dns_cache.get("fake-domain.com", None) is None

    # arcd.com is registered in dns server and should be saved to cache
    assert dns_client.check_domain_exists(target_domain="arcd.com")
    assert dns_client.dns_cache.get("arcd.com", None) is not None
