import pytest
from gymnasium import spaces

from primaite.game.agent.observations.file_system_observations import FileObservation, FolderObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.sim_container import Simulation


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_file_observation(simulation):
    """Test the file observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    # create a file on the pc
    file = pc.file_system.create_file(file_name="dog.png")

    dog_file_obs = FileObservation(
        where=["network", "nodes", pc.hostname, "file_system", "folders", "root", "files", "dog.png"]
    )

    assert dog_file_obs.space == spaces.Dict({"health_status": spaces.Discrete(6)})

    observation_state = dog_file_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 1  # good initial

    file.corrupt()
    observation_state = dog_file_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 1  # scan file so this changes

    file.scan()
    file.apply_timestep(0)  # apply time step
    observation_state = dog_file_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 3  # corrupted


def test_folder_observation(simulation):
    """Test the folder observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")
    # create a file and folder on the pc
    folder = pc.file_system.create_folder("test_folder")
    file = pc.file_system.create_file(file_name="dog.png", folder_name="test_folder")

    root_folder_obs = FolderObservation(
        where=["network", "nodes", pc.hostname, "file_system", "folders", "test_folder"]
    )

    observation_state = root_folder_obs.observe(simulation.describe_state())
    assert observation_state.get("FILES") is not None
    assert observation_state.get("health_status") == 1

    file.corrupt()  # corrupt just the file
    observation_state = root_folder_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 1  # scan folder to change this

    folder.scan()
    for i in range(folder.scan_duration + 1):
        folder.apply_timestep(i)  # apply as many timesteps as needed for a scan

    observation_state = root_folder_obs.observe(simulation.describe_state())
    assert observation_state.get("health_status") == 3  # file is corrupt therefore folder is corrupted too
