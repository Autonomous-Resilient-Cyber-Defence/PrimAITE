# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import pytest

from primaite import getLogger
from tests import TEST_CONFIG_ROOT

_LOGGER = getLogger(__name__)


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        [
            TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
            TEST_CONFIG_ROOT / "one_node_states_on_off_lay_down_config.yaml",
        ]
    ],
    indirect=True,
)
def test_rewards_are_being_penalised_at_each_step_function(
    temp_primaite_session,
):
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.

    The config 'one_node_states_on_off_lay_down_config.yaml' has 15 steps:
        On different steps, the laydown config has Pattern of Life (PoLs) which change a state of the node's attribute.
        For example, turning the nodes' file system state to CORRUPT from its original state GOOD.
        As a result these are the following rewards are activated:
            File System State: corrupt_should_be_good = -10 * 2 (on Steps 1 & 2)
            Hardware State: off_should_be_on = -10 * 2 (on Steps 4 & 5)
            Service State: compromised_should_be_good = -20 * 2 (on Steps 7 & 8)
            Software State: compromised_should_be_good = -20 * 2 (on Steps 10 & 11)

            The Pattern of Life (PoLs) last for 2 steps, so the agent is penalised twice.

    Note: This test run inherits from conftest.py where the PrimAITE environment is ran and the blue agent is hard-coded
    to do NOTHING on every step.
    We use Pattern of Lifes (PoLs) to change the nodes states and display that the agent is being penalised on all steps
    where the live network node differs from the network reference node.

    Total Reward: -10 + -10 + -10 + -10 + -20 + -20 + -20 + -20 = -120
    Step Count: 15

    For the 4 steps where this occurs the average reward is:
        Average Reward: -8 (-120 / 15)
    """
    with temp_primaite_session as session:
        session.evaluate()
        ev_rewards = session.eval_av_reward_per_episode_dict()
        assert ev_rewards[1] == -8.0
