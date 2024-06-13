from pathlib import Path
from typing import Union

import pytest
import yaml
from gymnasium import spaces

from primaite.game.agent.interface import ProxyAgent
from primaite.game.agent.observations.nic_observations import NICObservation
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    computer: Computer = example_network.get_node_by_hostname("client_1")
    server: Server = example_network.get_node_by_hostname("server_1")

    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    web_browser.run()

    # Install DNS Client service on computer
    computer.software_manager.install(DNSClient)
    dns_client: DNSClient = computer.software_manager.software.get("DNSClient")
    # set dns server
    dns_client.dns_server = server.network_interface[1].ip_address

    # Install Web Server service on server
    server.software_manager.install(WebServer)
    web_server_service: WebServer = server.software_manager.software.get("WebServer")
    web_server_service.start()

    # Install DNS Server service on server
    server.software_manager.install(DNSServer)
    dns_server: DNSServer = server.software_manager.software.get("DNSServer")
    # register arcd.com to DNS
    dns_server.dns_register(
        domain_name="arcd.com",
        domain_ip_address=server.network_interfaces[next(iter(server.network_interfaces))].ip_address,
    )

    return sim


def test_nic(simulation):
    """Test the NIC observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    nic: NIC = pc.network_interface[1]

    nic_obs = NICObservation(where=["network", "nodes", pc.hostname, "NICs", 1], include_nmne=True)

    assert nic_obs.space["nic_status"] == spaces.Discrete(3)
    assert nic_obs.space["NMNE"]["inbound"] == spaces.Discrete(4)
    assert nic_obs.space["NMNE"]["outbound"] == spaces.Discrete(4)

    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 1  # enabled
    assert observation_state.get("NMNE") is not None
    assert observation_state["NMNE"].get("inbound") == 0
    assert observation_state["NMNE"].get("outbound") == 0

    nic.disable()
    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 2  # disabled


def test_nic_categories(simulation):
    """Test the NIC observation nmne count categories."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    nic_obs = NICObservation(where=["network", "nodes", pc.hostname, "NICs", 1], include_nmne=True)

    assert nic_obs.high_nmne_threshold == 10  # default
    assert nic_obs.med_nmne_threshold == 5  # default
    assert nic_obs.low_nmne_threshold == 0  # default


@pytest.mark.skip(reason="Feature not implemented yet")
def test_config_nic_categories(simulation):
    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    nic_obs = NICObservation(
        where=["network", "nodes", pc.hostname, "NICs", 1],
        low_nmne_threshold=3,
        med_nmne_threshold=6,
        high_nmne_threshold=9,
        include_nmne=True,
    )

    assert nic_obs.high_nmne_threshold == 9
    assert nic_obs.med_nmne_threshold == 6
    assert nic_obs.low_nmne_threshold == 3

    with pytest.raises(Exception):
        # should throw an error
        NICObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=9,
            med_nmne_threshold=6,
            high_nmne_threshold=9,
            include_nmne=True,
        )

    with pytest.raises(Exception):
        # should throw an error
        NICObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=3,
            med_nmne_threshold=9,
            high_nmne_threshold=9,
            include_nmne=True,
        )


def test_nic_monitored_traffic(simulation):
    monitored_traffic = {"icmp": ["NONE"], "tcp": ["DNS"]}

    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    pc2: Computer = simulation.network.get_node_by_hostname("client_2")

    nic_obs = NICObservation(
        where=["network", "nodes", pc.hostname, "NICs", 1], include_nmne=True, monitored_traffic=monitored_traffic
    )

    simulation.pre_timestep(0)  # apply timestep to whole sim
    simulation.apply_timestep(0)  # apply timestep to whole sim
    traffic_obs = nic_obs.observe(simulation.describe_state()).get("TRAFFIC")

    assert traffic_obs["icmp"]["inbound"] == 0
    assert traffic_obs["icmp"]["outbound"] == 0

    # send a ping
    pc.ping(target_ip_address=pc2.network_interface[1].ip_address)
    traffic_obs = nic_obs.observe(simulation.describe_state()).get("TRAFFIC")

    assert traffic_obs["icmp"]["inbound"] == 1
    assert traffic_obs["icmp"]["outbound"] == 1

    simulation.pre_timestep(1)  # apply timestep to whole sim
    simulation.apply_timestep(1)  # apply timestep to whole sim
    traffic_obs = nic_obs.observe(simulation.describe_state()).get("TRAFFIC")

    assert traffic_obs["icmp"]["inbound"] == 0
    assert traffic_obs["icmp"]["outbound"] == 0
    assert traffic_obs["tcp"][53]["inbound"] == 0
    assert traffic_obs["tcp"][53]["outbound"] == 0

    # send a database query
    browser: WebBrowser = pc.software_manager.software.get("WebBrowser")
    browser.target_url = f"http://arcd.com/"
    browser.get_webpage()

    traffic_obs = nic_obs.observe(simulation.describe_state()).get("TRAFFIC")
    assert traffic_obs["icmp"]["inbound"] == 0
    assert traffic_obs["icmp"]["outbound"] == 0
    assert traffic_obs["tcp"][53]["inbound"] == 0
    assert traffic_obs["tcp"][53]["outbound"] == 1  # getting a webpage sent a dns request out

    simulation.pre_timestep(2)  # apply timestep to whole sim
    simulation.apply_timestep(2)  # apply timestep to whole sim
    traffic_obs = nic_obs.observe(simulation.describe_state()).get("TRAFFIC")

    assert traffic_obs["icmp"]["inbound"] == 0
    assert traffic_obs["icmp"]["outbound"] == 0
    assert traffic_obs["tcp"][53]["inbound"] == 0
    assert traffic_obs["tcp"][53]["outbound"] == 0


def test_nic_monitored_traffic_config():
    """Test that the config loads the monitored traffic config correctly."""
    game: PrimaiteGame = load_config(BASIC_CONFIG)

    # should have icmp and DNS
    defender_agent: ProxyAgent = game.agents.get("defender")
    cur_obs = defender_agent.observation_manager.current_observation

    assert cur_obs["NODES"]["HOST0"]["NICS"][1]["TRAFFIC"] == {
        "icmp": {"inbound": 0, "outbound": 0},
        "tcp": {53: {"inbound": 0, "outbound": 0}},
    }
