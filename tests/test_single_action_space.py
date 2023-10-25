# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import time

import pytest

# from primaite.acl.acl_rule import ACLRule
# from primaite.common.enums import HardwareState
# from primaite.environment.primaite_env import Primaite
from tests import TEST_CONFIG_ROOT


@pytest.skip("Deprecated")
def run_generic_set_actions(env: Primaite):
    """Run against a generic agent with specified blue agent actions."""
    # Reset the environment at the start of the episode
    # env.reset()
    training_config = env.training_config
    for episode in range(0, training_config.num_train_episodes):
        for step in range(0, training_config.num_train_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            action = 0
            # print("Episode:", episode, "\nStep:", step)
            if step == 5:
                # [1, 1, 2, 1, 1, 1, 1(position)]
                # Creates an ACL rule
                # Allows traffic from server_1 to node_1 on port FTP
                action = 56
            elif step == 7:
                # [1, 1, 2, 0] Node Action
                # Sets Node 1 Hardware State to OFF
                # Does not resolve any service
                action = 128
            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(training_config.time_delay / 1000)

        # Reset the environment at the end of the episode
        # env.reset()

    # env.close()


@pytest.skip("Deprecated")
@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        [
            TEST_CONFIG_ROOT / "single_action_space_main_config.yaml",
            TEST_CONFIG_ROOT / "single_action_space_lay_down_config.yaml",
        ]
    ],
    indirect=True,
)
def test_single_action_space_is_valid(temp_primaite_session):
    """Test single action space is valid."""
    # TODO: Refactor this at some point to build a custom ACL Hardcoded
    #  Agent and then patch the AgentIdentifier Enum class so that it
    #  has ACL_AGENT. This then allows us to set the agent identified in
    #  the main config and is a bit cleaner.
    with temp_primaite_session as session:
        env = session.env

        run_generic_set_actions(env)
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
            elif len(dict_item) == 7:
                contains_acl_actions = True
        # If both are there then the ANY action type is working
        if contains_node_actions and contains_acl_actions:
            both_action_spaces = True
        # Check condition should be True
        assert both_action_spaces


@pytest.skip("Deprecated")
@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        [
            TEST_CONFIG_ROOT / "single_action_space_fixed_blue_actions_main_config.yaml",
            TEST_CONFIG_ROOT / "single_action_space_lay_down_config.yaml",
        ]
    ],
    indirect=True,
)
def test_agent_is_executing_actions_from_both_spaces(temp_primaite_session):
    """Test to ensure the blue agent is carrying out both kinds of operations (NODE & ACL)."""
    # TODO: Refactor this at some point to build a custom ACL Hardcoded
    #  Agent and then patch the AgentIdentifier Enum class so that it
    #  has ACL_AGENT. This then allows us to set the agent identified in
    #  the main config and is a bit cleaner.
    with temp_primaite_session as session:
        env = session.env
        # Run environment with specified fixed blue agent actions only
        run_generic_set_actions(env)
        # Retrieve hardware state of computer_1 node in laydown config
        # Agent turned this off in Step 5
        computer_node_hardware_state = env.nodes["1"].hardware_state
        # Retrieve the Access Control List object stored by the environment at the end of the episode
        access_control_list = env.acl
        # Use the Access Control List object acl object attribute to get dictionary
        # Use dictionary.values() to get total list of all items in the dictionary
        acl_rules_list = access_control_list.acl
        # Length of this list tells you how many items are in the dictionary
        # This number is the frequency of Access Control Rules in the environment
        # In the scenario, we specified that the agent should create only 1 acl rule
        # This 1 rule added to the implicit deny means there should be 2 rules in total.
        rules_count = 0
        for rule in acl_rules_list:
            if isinstance(rule, ACLRule):
                rules_count += 1
        # Therefore these statements below MUST be true
        assert computer_node_hardware_state == HardwareState.OFF
        assert rules_count == 2
