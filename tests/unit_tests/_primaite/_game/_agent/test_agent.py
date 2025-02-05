from primaite.game.agent.observations.file_system_observations import FileObservation
from primaite.game.agent.observations.observation_manager import NullObservation
from primaite.game.agent.scripted_agents.random_agent import RandomAgent


def test_creating_empty_agent():
    agent = RandomAgent()
    assert len(agent.action_manager.action_map) == 0
    assert isinstance(agent.observation_manager.obs, NullObservation)
    assert len(agent.reward_function.reward_components) == 0


def test_creating_agent_from_dict():
    action_config = {
        "action_map": {
            0: {"action": "do-nothing", "options": {}},
            1: {
                "action": "node-application-execute",
                "options": {"node_name": "client", "application_name": "database"},
            },
        }
    }
    observation_config = {
        "type": "file",
        "options": {
            "file_name": "dog.pdf",
            "include_num_access": False,
            "file_system_requires_scan": False,
        },
    }
    reward_config = {
        "reward_components": [
            {
                "type": "database-file-integrity",
                "weight": 0.3,
                "options": {"node_hostname": "server", "folder_name": "database", "file_name": "database.db"},
            }
        ]
    }
    agent = RandomAgent(
        config={
            "ref": "random_agent",
            "team": "BLUE",
            "action_space": action_config,
            "observation_space": observation_config,
            "reward_function": reward_config,
        }
    )

    assert len(agent.action_manager.action_map) == 2
    assert isinstance(agent.observation_manager.obs, FileObservation)
    assert len(agent.reward_function.reward_components) == 1
