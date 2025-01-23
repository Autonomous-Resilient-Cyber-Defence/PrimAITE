# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.game.agent.observations.firewall_observation import FirewallObservation
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


def check_default_rules(acl_obs):
    assert len(acl_obs) == 7
    assert all(acl_obs[i]["position"] == i - 1 for i in range(1, 8))
    assert all(acl_obs[i]["permission"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["source_ip_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["source_wildcard_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["source_port_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["dest_ip_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["dest_wildcard_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["dest_port_id"] == 0 for i in range(1, 8))
    assert all(acl_obs[i]["protocol_id"] == 0 for i in range(1, 8))


def test_firewall_observation():
    """Test adding/removing acl rules and enabling/disabling ports."""
    net = Network()
    firewall_cfg = {"type": "firewall", "hostname": "firewall", "opertating_state": NodeOperatingState.ON}
    firewall = Firewall.from_config(config=firewall_cfg)
    firewall_observation = FirewallObservation(
        where=[],
        num_rules=7,
        ip_list=["10.0.0.1", "10.0.0.2"],
        wildcard_list=["0.0.0.255", "0.0.0.1"],
        port_list=[80, 53],
        protocol_list=["tcp"],
        include_users=False,
    )

    observation = firewall_observation.observe(firewall.describe_state())
    assert "ACL" in observation
    assert "PORTS" in observation
    assert "INTERNAL" in observation["ACL"]
    assert "EXTERNAL" in observation["ACL"]
    assert "DMZ" in observation["ACL"]
    assert "INBOUND" in observation["ACL"]["INTERNAL"]
    assert "OUTBOUND" in observation["ACL"]["INTERNAL"]
    assert "INBOUND" in observation["ACL"]["EXTERNAL"]
    assert "OUTBOUND" in observation["ACL"]["EXTERNAL"]
    assert "INBOUND" in observation["ACL"]["DMZ"]
    assert "OUTBOUND" in observation["ACL"]["DMZ"]
    all_acls = (
        observation["ACL"]["INTERNAL"]["INBOUND"],
        observation["ACL"]["INTERNAL"]["OUTBOUND"],
        observation["ACL"]["EXTERNAL"]["INBOUND"],
        observation["ACL"]["EXTERNAL"]["OUTBOUND"],
        observation["ACL"]["DMZ"]["INBOUND"],
        observation["ACL"]["DMZ"]["OUTBOUND"],
    )
    for acl_obs in all_acls:
        check_default_rules(acl_obs)

    # add a rule to the internal inbound and check that the observation is correct
    firewall.internal_inbound_acl.add_rule(
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

    observation = firewall_observation.observe(firewall.describe_state())
    observed_rule = observation["ACL"]["INTERNAL"]["INBOUND"][5]
    assert observed_rule["position"] == 4
    assert observed_rule["permission"] == 2
    assert observed_rule["source_ip_id"] == 2
    assert observed_rule["source_wildcard_id"] == 3
    assert observed_rule["source_port_id"] == 2
    assert observed_rule["dest_ip_id"] == 3
    assert observed_rule["dest_wildcard_id"] == 3
    assert observed_rule["dest_port_id"] == 2
    assert observed_rule["protocol_id"] == 2

    # check that none of the other acls have changed
    all_acls = (
        observation["ACL"]["INTERNAL"]["OUTBOUND"],
        observation["ACL"]["EXTERNAL"]["INBOUND"],
        observation["ACL"]["EXTERNAL"]["OUTBOUND"],
        observation["ACL"]["DMZ"]["INBOUND"],
        observation["ACL"]["DMZ"]["OUTBOUND"],
    )
    for acl_obs in all_acls:
        check_default_rules(acl_obs)

    # remove the rule and check that the observation is correct
    firewall.internal_inbound_acl.remove_rule(5)
    observation = firewall_observation.observe(firewall.describe_state())
    all_acls = (
        observation["ACL"]["INTERNAL"]["INBOUND"],
        observation["ACL"]["INTERNAL"]["OUTBOUND"],
        observation["ACL"]["EXTERNAL"]["INBOUND"],
        observation["ACL"]["EXTERNAL"]["OUTBOUND"],
        observation["ACL"]["DMZ"]["INBOUND"],
        observation["ACL"]["DMZ"]["OUTBOUND"],
    )
    for acl_obs in all_acls:
        check_default_rules(acl_obs)

    # check that there are three ports in the observation
    assert len(observation["PORTS"]) == 3

    # check that the ports are all disabled
    assert all(observation["PORTS"][i]["operating_status"] == 2 for i in range(1, 4))

    # connect a switch to the firewall and check that only the correct port is updated
    switch: Switch = Switch.from_config(config={"type": "switch", "hostname":"switch", "num_ports":1, "operating_state":NodeOperatingState.ON})
    link = net.connect(firewall.network_interface[1], switch.network_interface[1])
    assert firewall.network_interface[1].enabled
    observation = firewall_observation.observe(firewall.describe_state())
    assert observation["PORTS"][1]["operating_status"] == 1
    assert all(observation["PORTS"][i]["operating_status"] == 2 for i in range(2, 4))

    # disable the port and check that the operating status is updated
    firewall.network_interface[1].disable()
    assert not firewall.network_interface[1].enabled
    observation = firewall_observation.observe(firewall.describe_state())
    assert all(observation["PORTS"][i]["operating_status"] == 2 for i in range(1, 4))
