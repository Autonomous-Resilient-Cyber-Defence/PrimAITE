# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router, RouterARP
from primaite.simulator.system.services.arp.arp import ARP
from primaite.utils.validation.port import PORT_LOOKUP
from tests.integration_tests.network.test_routing import multi_hop_network


def test_arp_from_host_to_default_gateway(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    router_1 = multi_hop_network.get_node_by_hostname("router_1")

    pc_a_arp: ARP = pc_a.software_manager.arp

    expected_result = router_1.network_interface[2].mac_address
    actual_result = pc_a_arp.get_arp_cache_mac_address(router_1.network_interface[2].ip_address)

    assert actual_result == expected_result


def test_arp_from_router_to_router(multi_hop_network):
    router_1 = multi_hop_network.get_node_by_hostname("router_1")
    router_2 = multi_hop_network.get_node_by_hostname("router_2")

    router_1_arp: RouterARP = router_1.software_manager.arp

    expected_result = router_2.network_interface[1].mac_address
    actual_result = router_1_arp.get_arp_cache_mac_address(router_2.network_interface[1].ip_address)

    assert actual_result == expected_result


def test_arp_fails_for_broadcast_address_between_routers(multi_hop_network):
    router_1 = multi_hop_network.get_node_by_hostname("router_1")

    router_1_arp: RouterARP = router_1.software_manager.arp

    expected_result = None
    actual_result = router_1_arp.get_arp_cache_mac_address(router_1.network_interface[1].ip_network.broadcast_address)

    assert actual_result == expected_result


def test_arp_fails_for_network_address_between_routers(multi_hop_network):
    router_1 = multi_hop_network.get_node_by_hostname("router_1")

    router_1_arp: RouterARP = router_1.software_manager.arp

    expected_result = None
    actual_result = router_1_arp.get_arp_cache_mac_address(router_1.network_interface[1].ip_network.network_address)

    assert actual_result == expected_result


def test_arp_not_affected_by_acl(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    router_1: Router = multi_hop_network.get_node_by_hostname("router_1")

    # Add explicit rule to block ARP traffic. This shouldn't actually stop ARP traffic
    # as it operates a different layer within the network.
    router_1.acl.add_rule(action=ACLAction.DENY, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=23)

    pc_a_arp: ARP = pc_a.software_manager.arp

    expected_result = router_1.network_interface[2].mac_address
    actual_result = pc_a_arp.get_arp_cache_mac_address(router_1.network_interface[2].ip_address)

    assert actual_result == expected_result
