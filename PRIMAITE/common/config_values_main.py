# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
The config class
"""

class config_values_main(object):
    """
    Class to hold main config values
    """

    def __init__(self):
        """
        Init
        """

        # Generic
        self.agent_identifier = ""                  # the agent in use
        self.num_episodes = 0                       # number of episodes to train over
        self.num_steps = 0                          # number of steps in an episode
        self.time_delay = 0                         # delay between steps (ms) - applies to generic agents only
        self.config_filename_use_case = ""          # the filename for the Use Case config file

        # Environment
        self.observation_space_high_value = 0       # The high value for the observation space

        # Reward values
        # Generic
        self.all_ok = 0 
        # Node Operating State
        self.off_should_be_on = 0
        self.off_should_be_resetting = 0
        self.on_should_be_off = 0
        self.on_should_be_resetting = 0
        self.resetting_should_be_on = 0
        self.resetting_should_be_off = 0 
        # Node O/S or Service State
        self.good_should_be_patching = 0
        self.good_should_be_compromised = 0
        self.good_should_be_overwhelmed = 0
        self.patching_should_be_good = 0
        self.patching_should_be_compromised = 0
        self.patching_should_be_overwhelmed = 0
        self.compromised_should_be_good = 0
        self.compromised_should_be_patching = 0
        self.compromised_should_be_overwhelmed = 0
        self.compromised = 0     
        self.overwhelmed_should_be_good = 0
        self.overwhelmed_should_be_patching = 0
        self.overwhelmed_should_be_compromised = 0
        self.overwhelmed = 0
        # IER status
        self.red_ier_running = 0
        self.green_ier_blocked = 0

        # Patching / Reset
        self.os_patching_duration = 0                         # The time taken to patch the OS
        self.node_reset_duration = 0                          # The time taken to reset a node (hardware)
        self.service_patching_duration = 0                    # The time taken to patch a service

