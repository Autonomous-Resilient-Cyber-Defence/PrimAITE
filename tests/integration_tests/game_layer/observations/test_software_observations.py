# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest
from gymnasium import spaces

from primaite.game.agent.observations.software_observation import ApplicationObservation, ServiceObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.ntp.ntp_server import NTPServer


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_service_observation(simulation):
    """Test the service observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    # install software on the computer
    pc.software_manager.install(NTPServer)

    ntp_server = pc.software_manager.software.get("NTPServer")
    assert ntp_server

    service_obs = ServiceObservation(
        where=["network", "nodes", pc.hostname, "services", "NTPServer"], services_requires_scan=True
    )

    assert service_obs.space["operating_status"] == spaces.Discrete(7)
    assert service_obs.space["health_status"] == spaces.Discrete(5)

    observation_state = service_obs.observe(simulation.describe_state())

    assert observation_state.get("health_status") == 0
    assert observation_state.get("operating_status") == 1  # running

    ntp_server.restart()
    observation_state = service_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 0
    assert observation_state.get("operating_status") == 6  # resetting


def test_application_observation(simulation):
    """Test the application observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    # install software on the computer
    pc.software_manager.install(DatabaseClient)

    web_browser: WebBrowser = pc.software_manager.software.get("WebBrowser")
    assert web_browser

    app_obs = ApplicationObservation(
        where=["network", "nodes", pc.hostname, "applications", "WebBrowser"], applications_requires_scan=True
    )

    web_browser.close()
    observation_state = app_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 0
    assert observation_state.get("operating_status") == 2  # stopped
    assert observation_state.get("num_executions") == 0

    web_browser.run()
    web_browser.scan()  # scan to update health status
    web_browser.get_webpage("test")
    observation_state = app_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 1
    assert observation_state.get("operating_status") == 1  # running
    assert observation_state.get("num_executions") == 1


def test_application_executions_categories(simulation):
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    app_obs = ApplicationObservation(
        where=["network", "nodes", pc.hostname, "applications", "WebBrowser"],
        applications_requires_scan=False,
        thresholds={"app_executions": {"low": 3, "medium": 6, "high": 9}},
    )

    assert app_obs.high_threshold == 9
    assert app_obs.med_threshold == 6
    assert app_obs.low_threshold == 3

    with pytest.raises(Exception):
        # should throw an error
        ApplicationObservation(
            where=["network", "nodes", pc.hostname, "applications", "WebBrowser"],
            applications_requires_scan=False,
            thresholds={"app_executions": {"low": 9, "medium": 6, "high": 9}},
        )

    with pytest.raises(Exception):
        # should throw an error
        ApplicationObservation(
            where=["network", "nodes", pc.hostname, "applications", "WebBrowser"],
            applications_requires_scan=False,
            thresholds={"app_executions": {"low": 3, "medium": 9, "high": 9}},
        )
