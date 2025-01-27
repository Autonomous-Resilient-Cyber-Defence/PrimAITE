# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from pprint import pprint

from primaite.game.agent.observations.acl_observation import ACLObservation
from primaite.game.agent.observations.nic_observations import PortObservation
from primaite.game.agent.observations.router_observation import RouterObservation
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.sim_container import Simulation
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


def test_router_observation():
    """Test adding/removing acl rules and enabling/disabling ports."""
    net = Network()
    router = Router.from_config(
        config={"type": "router", "hostname": "router", "num_ports": 5, "operating_state": NodeOperatingState.ON}
    )

    ports = [PortObservation(where=["NICs", i]) for i in range(1, 6)]
    acl = ACLObservation(
        where=["acl", "acl"],
        num_rules=7,
        ip_list=["10.0.0.1", "10.0.0.2"],
        wildcard_list=["0.0.0.255", "0.0.0.1"],
        port_list=[80, 53],
        protocol_list=["tcp"],
    )
    router_observation = RouterObservation(where=[], ports=ports, num_ports=8, acl=acl, include_users=False)

    # Observe the state using the RouterObservation instance
    observed_output = router_observation.observe(router.describe_state())

    # Check that the right number of ports and acls are in the router observation
    assert len(observed_output["PORTS"]) == 8
    assert len(observed_output["ACL"]) == 7

    # Add an ACL rule to the router
    router.acl.add_rule(
        action=ACLAction.DENY,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_ip_address="10.0.0.1",
        src_wildcard_mask="0.0.0.1",
        dst_ip_address="10.0.0.2",
        dst_wildcard_mask="0.0.0.1",
        src_port=PORT_LOOKUP["HTTP"],
        dst_port=PORT_LOOKUP["HTTP"],
        position=5,
    )
    # Observe the state using the RouterObservation instance
    observed_output = router_observation.observe(router.describe_state())
    observed_rule = observed_output["ACL"][5]
    assert observed_rule["position"] == 4
    assert observed_rule["permission"] == 2
    assert observed_rule["source_ip_id"] == 2
    assert observed_rule["source_wildcard_id"] == 3
    assert observed_rule["source_port_id"] == 2
    assert observed_rule["dest_ip_id"] == 3
    assert observed_rule["dest_wildcard_id"] == 3
    assert observed_rule["dest_port_id"] == 2
    assert observed_rule["protocol_id"] == 2

    # Add an ACL rule with ALL/NONE values and check that the observation is correct
    router.acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=None,
        src_ip_address=None,
        src_wildcard_mask=None,
        dst_ip_address=None,
        dst_wildcard_mask=None,
        src_port=None,
        dst_port=None,
        position=2,
    )
    observed_output = router_observation.observe(router.describe_state())
    observed_rule = observed_output["ACL"][2]
    assert observed_rule["position"] == 1
    assert observed_rule["permission"] == 1
    assert observed_rule["source_ip_id"] == 1
    assert observed_rule["source_wildcard_id"] == 1
    assert observed_rule["source_port_id"] == 1
    assert observed_rule["dest_ip_id"] == 1
    assert observed_rule["dest_wildcard_id"] == 1
    assert observed_rule["dest_port_id"] == 1
    assert observed_rule["protocol_id"] == 1

    # Check that the router ports are all disabled
    assert all(observed_output["PORTS"][i]["operating_status"] == 2 for i in range(1, 6))

    # connect a switch to the router and check that only the correct port is updated
    switch: Switch = Switch.from_config(
        config={"type": "switch", "hostname": "switch", "num_ports": 1, "operating_state": NodeOperatingState.ON}
    )
    link = net.connect(router.network_interface[1], switch.network_interface[1])
    assert router.network_interface[1].enabled
    observed_output = router_observation.observe(router.describe_state())
    assert observed_output["PORTS"][1]["operating_status"] == 1
    assert all(observed_output["PORTS"][i]["operating_status"] == 2 for i in range(2, 6))

    # disable the port and check that the operating status is updated
    router.network_interface[1].disable()
    assert not router.network_interface[1].enabled
    observed_output = router_observation.observe(router.describe_state())
    assert all(observed_output["PORTS"][i]["operating_status"] == 2 for i in range(1, 6))

    # Check that ports that are out of range are shown as unused
    observed_output = router_observation.observe(router.describe_state())
    assert observed_output["PORTS"][6]["operating_status"] == 0
    assert observed_output["PORTS"][7]["operating_status"] == 0
    assert observed_output["PORTS"][8]["operating_status"] == 0
