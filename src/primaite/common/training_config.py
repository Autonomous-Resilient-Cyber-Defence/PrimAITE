# # Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
# """The config class."""
# from dataclasses import dataclass
#
# from primaite.common.enums import ActionType
#
#
# @dataclass()
# class TrainingConfig:
#     """Class to hold main config values."""
#
#     # Generic
#     agent_identifier: str  # The Red Agent algo/class to be used
#     action_type: ActionType  # type of action to use (NODE/ACL/ANY)
#     num_episodes: int  # number of episodes to train over
#     num_steps: int  # number of steps in an episode
#     time_delay: int  # delay between steps (ms) - applies to generic agents only
#     # file
#     session_type: str  # the session type to run (TRAINING or EVALUATION)
#     load_agent: str  # Determine whether to load an agent from file
#     agent_load_file: str  # File path and file name of agent if you're loading one in
#
#     # Environment
#     observation_space_high_value: int  # The high value for the observation space
#
#     # Reward values
#     # Generic
#     all_ok: int
#     # Node Hardware State
#     off_should_be_on: int
#     off_should_be_resetting: int
#     on_should_be_off: int
#     on_should_be_resetting: int
#     resetting_should_be_on: int
#     resetting_should_be_off: int
#     resetting: int
#     # Node Software or Service State
#     good_should_be_patching: int
#     good_should_be_compromised: int
#     good_should_be_overwhelmed: int
#     patching_should_be_good: int
#     patching_should_be_compromised: int
#     patching_should_be_overwhelmed: int
#     patching: int
#     compromised_should_be_good: int
#     compromised_should_be_patching: int
#     compromised_should_be_overwhelmed: int
#     compromised: int
#     overwhelmed_should_be_good: int
#     overwhelmed_should_be_patching: int
#     overwhelmed_should_be_compromised: int
#     overwhelmed: int
#     # Node File System State
#     good_should_be_repairing: int
#     good_should_be_restoring: int
#     good_should_be_corrupt: int
#     good_should_be_destroyed: int
#     repairing_should_be_good: int
#     repairing_should_be_restoring: int
#     repairing_should_be_corrupt: int
#     repairing_should_be_destroyed: int  # Repairing does not fix destroyed state - you need to restore
#
#     repairing: int
#     restoring_should_be_good: int
#     restoring_should_be_repairing: int
#     restoring_should_be_corrupt: int  # Not the optimal method (as repair will fix corruption)
#
#     restoring_should_be_destroyed: int
#     restoring: int
#     corrupt_should_be_good: int
#     corrupt_should_be_repairing: int
#     corrupt_should_be_restoring: int
#     corrupt_should_be_destroyed: int
#     corrupt: int
#     destroyed_should_be_good: int
#     destroyed_should_be_repairing: int
#     destroyed_should_be_restoring: int
#     destroyed_should_be_corrupt: int
#     destroyed: int
#     scanning: int
#     # IER status
#     red_ier_running: int
#     green_ier_blocked: int
#
#     # Patching / Reset
#     os_patching_duration: int  # The time taken to patch the OS
#     node_reset_duration: int  # The time taken to reset a node (hardware)
#     node_booting_duration = 0  # The Time taken to turn on the node
#     node_shutdown_duration = 0  # The time taken to turn off the node
#     service_patching_duration: int  # The time taken to patch a service
#     file_system_repairing_limit: int  # The time take to repair a file
#     file_system_restoring_limit: int  # The time take to restore a file
#     file_system_scanning_limit: int  # The time taken to scan the file system
#     # Patching / Reset
#
