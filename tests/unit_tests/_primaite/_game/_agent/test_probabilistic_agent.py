# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.game.agent.actions import ActionManager
from primaite.game.agent.observations.observation_manager import NestedObservation, ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.game.agent.scripted_agents.probabilistic_agent import ProbabilisticAgent
from primaite.game.game import PrimaiteGame, PrimaiteGameOptions


def test_probabilistic_agent():
    """
    Check that the probabilistic agent selects actions with approximately the right probabilities.

    Using a binomial probability calculator (https://www.wolframalpha.com/input/?i=binomial+distribution+calculator),
    we can generate some lower and upper bounds of how many times we expect the agent to take each action. These values
    were chosen to guarantee a less than 1 in a million chance of the test failing due to unlucky random number
    generation.
    """
    N_TRIALS = 10_000
    P_DO_NOTHING = 0.1
    P_node_application_execute = 0.3
    P_node_file_delete = 0.6
    MIN_DO_NOTHING = 850
    MAX_DO_NOTHING = 1150
    MIN_node_application_execute = 2800
    MAX_node_application_execute = 3200
    MIN_node_file_delete = 5750
    MAX_node_file_delete = 6250

    action_space_cfg = {
        "action_map": {
            0: {"action": "do-nothing", "options": {}},
            1: {
                "action": "node-application-execute",
                "options": {"node_name": "client_1", "application_name": "web-browser"},
            },
            2: {
                "action": "node-file-delete",
                "options": {"node_name": "client_1", "folder_name": "downloads", "file_name": "cat.png"},
            },
        },
    }

    game = PrimaiteGame()
    game.options = PrimaiteGameOptions(ports=[], protocols=[])

    pa_config = {
        "type": "probabilistic-agent",
        "ref": "probabilistic-agent",
        "team": "BLUE",
        "action_space": action_space_cfg,
        "agent_settings": {
            "action_probabilities": {0: P_DO_NOTHING, 1: P_node_application_execute, 2: P_node_file_delete},
        },
    }

    pa = ProbabilisticAgent.from_config(config=pa_config)

    do_nothing_count = 0
    node_application_execute_count = 0
    node_file_delete_count = 0
    for _ in range(N_TRIALS):
        a = pa.get_action(0)
        if a == ("do-nothing", {}):
            do_nothing_count += 1
        elif a == ("node-application-execute", {"node_name": "client_1", "application_name": "web-browser"}):
            node_application_execute_count += 1
        elif a == ("node-file-delete", {"node_name": "client_1", "folder_name": "downloads", "file_name": "cat.png"}):
            node_file_delete_count += 1
        else:
            raise AssertionError("Probabilistic agent produced an unexpected action.")

    assert MIN_DO_NOTHING < do_nothing_count < MAX_DO_NOTHING
    assert MIN_node_application_execute < node_application_execute_count < MAX_node_application_execute
    assert MIN_node_file_delete < node_file_delete_count < MAX_node_file_delete
