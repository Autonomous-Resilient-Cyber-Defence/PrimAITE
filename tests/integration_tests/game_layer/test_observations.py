# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from gymnasium import spaces

from primaite.game.agent.observations.file_system_observations import FileObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.sim_container import Simulation


def test_file_observation():
    sim = Simulation()
    pc = Computer(hostname="beep", ip_address="123.123.123.123", subnet_mask="255.255.255.0")
    sim.network.add_node(pc)
    f = pc.file_system.create_file(file_name="dog.png")

    state = sim.describe_state()

    dog_file_obs = FileObservation(
        where=["network", "nodes", pc.hostname, "file_system", "folders", "root", "files", "dog.png"],
        include_num_access=False,
        file_system_requires_scan=True,
    )
    assert dog_file_obs.observe(state) == {"health_status": 1}
    assert dog_file_obs.space == spaces.Dict({"health_status": spaces.Discrete(6)})


# TODO:
# def test_file_num_access():
#     ...
