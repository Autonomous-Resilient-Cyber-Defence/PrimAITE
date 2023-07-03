from datetime import datetime

from primaite.config.lay_down_config import data_manipulation_config_path
from primaite.environment.primaite_env import Primaite
from primaite.nodes.node_state_instruction_red import NodeStateInstructionRed
from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_temp_session_path


def run_generic(env, config_values):
    """Run against a generic agent."""
    # Reset the environment at the start of the episode
    env.reset()
    for episode in range(0, config_values.num_episodes):
        for step in range(0, config_values.num_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            # action = env.action_space.sample()
            action = 0

            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

        # Reset the environment at the end of the episode
        env.reset()

    env.close()


def test_random_red_agent_behaviour():
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.
    """
    list_of_node_instructions = []

    # RUN TWICE so we can make sure that red agent is randomised
    for i in range(2):
        """Takes a config path and returns the created instance of Primaite."""
        session_timestamp: datetime = datetime.now()
        session_path = _get_temp_session_path(session_timestamp)

        timestamp_str = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        env = Primaite(
            training_config_path=TEST_CONFIG_ROOT
            / "one_node_states_on_off_main_config.yaml",
            lay_down_config_path=data_manipulation_config_path(),
            transaction_list=[],
            session_path=session_path,
            timestamp_str=timestamp_str,
        )
        training_config = env.training_config
        training_config.num_steps = env.episode_steps

        run_generic(env, training_config)
        # add red pol instructions to list
        list_of_node_instructions.append(env.red_node_pol)

    # compare instructions to make sure that red instructions are truly random
    for index, instruction in enumerate(list_of_node_instructions):
        for key in list_of_node_instructions[index].keys():
            instruction: NodeStateInstructionRed = list_of_node_instructions[index][key]
            print(f"run {index}")
            print(f"{key} start step: {instruction.get_start_step()}")
            print(f"{key} end step: {instruction.get_end_step()}")
            print(f"{key} target node id: {instruction.get_target_node_id()}")
            print("")

    assert list_of_node_instructions[0].__ne__(list_of_node_instructions[1])
