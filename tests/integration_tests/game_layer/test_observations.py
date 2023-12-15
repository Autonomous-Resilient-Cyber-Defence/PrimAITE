from gymnasium import spaces

from primaite.game.agent.observations import FileObservation
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.sim_container import Simulation


def test_file_observation():
    sim = Simulation()
    pc = Computer(hostname="beep", ip_address="123.123.123.123", subnet_mask="255.255.255.0")
    sim.network.add_node(pc)
    f = pc.file_system.create_file(file_name="dog.png")

    state = sim.describe_state()

    dog_file_obs = FileObservation(
        where=["network", "nodes", pc.hostname, "file_system", "folders", "root", "files", "dog.png"]
    )
    assert dog_file_obs.observe(state) == {"health_status": 1}
    assert dog_file_obs.space == spaces.Dict({"health_status": spaces.Discrete(6)})
