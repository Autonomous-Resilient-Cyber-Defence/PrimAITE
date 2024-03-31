import pytest

from primaite.game.agent.observations.acl_observation import ACLObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_acl_observations(simulation):
    """Test the ACL rule observations."""
    router: Router = simulation.network.get_node_by_hostname("router_1")
    client_1: Computer = simulation.network.get_node_by_hostname("client_1")
    server: Computer = simulation.network.get_node_by_hostname("server_1")

    # quick set up of ntp
    client_1.software_manager.install(NTPClient)
    ntp_client: NTPClient = client_1.software_manager.software.get("NTPClient")
    ntp_client.configure(server.network_interface.get(1).ip_address)
    server.software_manager.install(NTPServer)

    # add router acl rule
    router.acl.add_rule(action=ACLAction.PERMIT, dst_port=Port.NTP, src_port=Port.NTP, position=1)

    acl_obs = ACLObservation(
        where=["network", "nodes", router.hostname, "acl", "acl"],
        node_ip_to_id={},
        ports=["NTP", "HTTP", "POSTGRES_SERVER"],
        protocols=["TCP", "UDP", "ICMP"],
    )

    observation_space = acl_obs.observe(simulation.describe_state())
    assert observation_space.get(1) is not None
    rule_obs = observation_space.get(1)  # this is the ACL Rule added to allow NTP
    assert rule_obs.get("position") == 0  # rule was put at position 1 (0 because counting from 1 instead of 1)
    assert rule_obs.get("permission") == 1  # permit = 1 deny = 2
    assert rule_obs.get("source_node_id") == 1  # applies to all source nodes
    assert rule_obs.get("dest_node_id") == 1  # applies to all destination nodes
    assert rule_obs.get("source_port") == 2  # NTP port is mapped to value 2 (1 = ALL, so 1+1 = 2 quik mafs)
    assert rule_obs.get("dest_port") == 2  # NTP port is mapped to value 2
    assert rule_obs.get("protocol") == 1  # 1 = No Protocol

    router.acl.remove_rule(1)

    observation_space = acl_obs.observe(simulation.describe_state())
    assert observation_space.get(1) is not None
    rule_obs = observation_space.get(1)  # this is the ACL Rule added to allow NTP
    assert rule_obs.get("position") == 0
    assert rule_obs.get("permission") == 0
    assert rule_obs.get("source_node_id") == 0
    assert rule_obs.get("dest_node_id") == 0
    assert rule_obs.get("source_port") == 0
    assert rule_obs.get("dest_port") == 0
    assert rule_obs.get("protocol") == 0
