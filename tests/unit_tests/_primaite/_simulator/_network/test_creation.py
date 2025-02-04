# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.creation import NetworkNodeAdder, OfficeLANAdder

param_names = ("lan_name", "subnet_base", "pcs_ip_block_start", "num_pcs", "include_router", "bandwidth")
param_vals = (
    ("CORP-NETWORK", 3, 10, 6, True, 45),
    ("OTHER-NETWORK", 10, 25, 26, True, 100),
    ("OTHER-NETWORK", 10, 25, 55, False, 100),
)
param_dicts = [dict(zip(param_names, vals)) for vals in param_vals]


def _assert_valid_creation(net: Network, lan_name, subnet_base, pcs_ip_block_start, num_pcs, include_router, bandwidth):
    """Assert that the network contains the correct nodes as described by config items"""
    num_switches = 1 if num_pcs <= 23 else num_pcs // 23 + 2
    num_routers = 1 if include_router else 0
    total_nodes = num_pcs + num_switches + num_routers

    assert all((n.config.hostname.endswith(lan_name) for n in net.nodes.values()))
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


@pytest.mark.parametrize("kwargs", param_dicts)
def test_office_lan_adder(kwargs):
    """Assert that adding an office lan via the python API works correctly."""
    net = Network()

    office_lan_config = OfficeLANAdder.ConfigSchema(
        lan_name=kwargs["lan_name"],
        subnet_base=kwargs["subnet_base"],
        pcs_ip_block_start=kwargs["pcs_ip_block_start"],
        num_pcs=kwargs["num_pcs"],
        include_router=kwargs["include_router"],
        bandwidth=kwargs["bandwidth"],
    )
    OfficeLANAdder.add_nodes_to_net(config=office_lan_config, network=net)

    _assert_valid_creation(net=net, **kwargs)


@pytest.mark.parametrize("kwargs", param_dicts)
def test_office_lan_from_config(kwargs):
    """Assert that the base class can add an office lan given a config dict."""
    net = Network()

    config = dict(
        type="office_lan",
        lan_name=kwargs["lan_name"],
        subnet_base=kwargs["subnet_base"],
        pcs_ip_block_start=kwargs["pcs_ip_block_start"],
        num_pcs=kwargs["num_pcs"],
        include_router=kwargs["include_router"],
        bandwidth=kwargs["bandwidth"],
    )

    NetworkNodeAdder.from_config(config=config, network=net)
    _assert_valid_creation(net=net, **kwargs)
