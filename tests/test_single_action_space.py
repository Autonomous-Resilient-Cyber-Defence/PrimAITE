import time

from primaite.common.enums import HardwareState
from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def run_generic_set_actions(env, config_values):
    """Run against a generic agent with specified blue agent actions."""
    # Reset the environment at the start of the episode
    # env.reset()
    for episode in range(0, config_values.num_episodes):
        for step in range(0, config_values.num_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            action = 0
            print("Episode:", episode, "\nStep:", step)
            if step == 5:
                # [1, 1, 2, 1, 1, 1]
                # Creates an ACL rule
                # Deny traffic from server_1 to node_1 on port FTP
                action = 7
            elif step == 7:
                # [1, 1, 2, 0] Node Action
                # Sets Node 1 Hardware State to OFF
                # Does not resolve any service
                action = 16
            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode
        # env.reset()

    # env.close()


def test_single_action_space_is_valid():
    """Test to ensure the blue agent is using the ACL action space and is carrying out both kinds of operations."""
    env, config_values = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "single_action_space_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "single_action_space_lay_down_config.yaml",
    )

    run_generic_set_actions(env, config_values)

    # Retrieve the action space dictionary values from environment
    env_action_space_dict = env.action_dict.values()
    # Flags to check the conditions of the action space
    contains_acl_actions = False
    contains_node_actions = False
    both_action_spaces = False
    # Loop through each element of the list (which is every value from the dictionary)
    for dict_item in env_action_space_dict:
        # Node action detected
        if len(dict_item) == 4:
            contains_node_actions = True
        # Link action detected
        elif len(dict_item) == 6:
            contains_acl_actions = True
    # If both are there then the ANY action type is working
    if contains_node_actions and contains_acl_actions:
        both_action_spaces = True
    # Check condition should be True
    assert both_action_spaces


def test_agent_is_executing_actions_from_both_spaces():
    """Test to ensure the blue agent is carrying out both kinds of operations (NODE & ACL)."""
    env, config_values = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT
        / "single_action_space_fixed_blue_actions_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "single_action_space_lay_down_config.yaml",
    )

    run_generic_set_actions(env, config_values)

    # Retrieve hardware state of computer_1 node in laydown config
    # Agent turned this off in Step 5
    computer_node_hardware_state = env.nodes["1"].hardware_state
    # Retrieve the Access Control List object stored by the environment at the end of the episode
    access_control_list = env.acl
    # Use the Access Control List object acl object attribute to get dictionary
    # Use dictionary.values() to get total list of all items in the dictionary
    acl_rules_list = access_control_list.acl.values()
    # Length of this list tells you how many items are in the dictionary
    # This number is the frequency of Access Control Rules in the environment
    # In the scenario, we specified that the agent should create only 1 acl rule
    num_of_rules = len(acl_rules_list)
    # Therefore these statements below MUST be true
    assert computer_node_hardware_state == HardwareState.OFF and num_of_rules == 1
