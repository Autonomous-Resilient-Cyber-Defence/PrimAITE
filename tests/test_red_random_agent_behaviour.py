from datetime import time, datetime

from primaite.environment.primaite_env import Primaite
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

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode
        env.reset()

    env.close()


def test_random_red_agent_behaviour():
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.
    """
    list_of_node_instructions = []
    for i in range(2):

        """Takes a config path and returns the created instance of Primaite."""
        session_timestamp: datetime = datetime.now()
        session_path = _get_temp_session_path(session_timestamp)

        timestamp_str = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        env = Primaite(
            training_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
            lay_down_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_lay_down_config.yaml",
            transaction_list=[],
            session_path=session_path,
            timestamp_str=timestamp_str,
        )
        training_config = env.training_config
        training_config.num_steps = env.episode_steps

        # TOOD: This needs t be refactored to happen outside. Should be part of
        # a main Session class.
        if training_config.agent_identifier == "GENERIC":
            run_generic(env, training_config)
        all_red_actions = env.red_node_pol
        list_of_node_instructions.append(all_red_actions)

    # assert not (list_of_node_instructions[0].__eq__(list_of_node_instructions[1]))
    print(list_of_node_instructions[0]["1"].get_start_step())
    print(list_of_node_instructions[0]["1"].get_end_step())
    print(list_of_node_instructions[0]["1"].get_target_node_id())
    print(list_of_node_instructions[1]["1"].get_start_step())
    print(list_of_node_instructions[1]["1"].get_end_step())
    print(list_of_node_instructions[1]["1"].get_target_node_id())
    assert list_of_node_instructions[0].__ne__(list_of_node_instructions[1])
