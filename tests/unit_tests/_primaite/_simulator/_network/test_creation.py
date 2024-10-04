# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.creation import OfficeLANAdder


@pytest.mark.parametrize(
    ("lan_name", "subnet_base", "pcs_ip_block_start", "num_pcs", "include_router", "bandwidth"),
    (
        ("CORP-NETWORK", 3, 10, 6, True, 45),
        ("OTHER-NETWORK", 10, 25, 26, True, 100),
        ("OTHER-NETWORK", 10, 25, 55, False, 100),
    ),
)
def test_office_lan_adder(lan_name, subnet_base, pcs_ip_block_start, num_pcs, include_router, bandwidth):
    net = Network()

    office_lan_config = OfficeLANAdder.ConfigSchema(
        lan_name=lan_name,
        subnet_base=subnet_base,
        pcs_ip_block_start=pcs_ip_block_start,
        num_pcs=num_pcs,
        include_router=include_router,
        bandwidth=bandwidth,
    )
    OfficeLANAdder.add_nodes_to_net(config=office_lan_config, network=net)

    num_switches = 1 if num_pcs <= 23 else num_pcs // 23 + 2
    num_routers = 1 if include_router else 0
    total_nodes = num_pcs + num_switches + num_routers

    assert all((n.hostname.endswith(lan_name) for n in net.nodes.values()))
    assert len(net.computer_nodes) == num_pcs
    assert len(net.switch_nodes) == num_switches
    assert len(net.router_nodes) == num_routers
    assert len(net.nodes) == total_nodes
    assert all(
        [str(n.network_interface[1].ip_address).startswith(f"192.168.{subnet_base}") for n in net.computer_nodes]
    )
    # check that computers occupy address range 192.168.3.10 - 192.168.3.16
    computer_ip_last_octets = {str(n.network_interface[1].ip_address).split(".")[-1] for n in net.computer_nodes}
    assert computer_ip_last_octets == {str(i) for i in range(pcs_ip_block_start, pcs_ip_block_start + num_pcs)}
