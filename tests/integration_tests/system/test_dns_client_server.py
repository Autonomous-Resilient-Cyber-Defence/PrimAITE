from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.services.dns_client import DNSClient
from primaite.simulator.system.services.dns_server import DNSServer


def test_dns_client_server(uc2_network):
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    domain_controller: Server = uc2_network.get_node_by_hostname("domain_controller")

    dns_client: DNSClient = client_1.software_manager.software["DNSClient"]
    dns_server: DNSServer = domain_controller.software_manager.software["DNSServer"]

    # register a domain to web server
    dns_server.dns_register("real-domain.com", IPv4Address("192.168.1.12"))

    dns_server.show()

    dns_client.check_domain_exists(target_domain="real-domain.com", dest_ip_address=IPv4Address("192.168.1.14"))

    # should register the domain in the client cache
    assert dns_client.dns_cache.get("real-domain.com") is not None
