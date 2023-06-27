from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_rewards_are_being_penalised_at_each_step_function():
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.
    """
    env = _get_primaite_env_from_config(
        training_config_path=TEST_CONFIG_ROOT
        / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "one_node_states_on_off_lay_down_config.yaml",
    )

    """
    The config 'one_node_states_on_off_lay_down_config.yaml' has 15 steps:
        On different steps, the laydown config has Pattern of Life (PoLs) which change a state of the node's attribute.
        For example, turning the nodes' file system state to CORRUPT from its original state GOOD.
        As a result these are the following rewards are activated:
            File System State: corrupt_should_be_good = -10 * 2 (on Steps 1 = 3)
            Hardware State: off_should_be_on = -10 * 2 (on Steps 4 - 6)
            Service State: compromised_should_be_good = -20 * 2 (on Steps 7 - 9)
            Software State: compromised_should_be_good = -20 * 2 (on Steps 10 - 12)

            The Pattern of Life (PoLs) last for 2 steps, so the agent is penalised twice.

    Note: This test run inherits conftest.py where the PrimAITE environment is ran and the blue agent is hard-coded
    to do NOTHING on every step so we use Pattern of Lifes (PoLs) to change the nodes states and display that the agent
    is being penalised on every step where the live network node differs from the network reference node.

    Total Reward: -10 + -10 + -10 + -10 + -20 + -20 + -20 + -20 = -120
    Step Count: 15

    For the 4 steps where this occurs the average reward is:
        Average Reward: -8 (-120 / 15)
    """
    assert env.average_reward == -8.0
