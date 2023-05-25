# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The Transaction class."""


class Transaction(object):
    """Transaction class."""

    def __init__(self, _timestamp, _agent_identifier, _episode_number, _step_number):
        """
        Init.

        Args:
            _timestamp: The time this object was created
            _agent_identifier: An identifier for the agent in use
            _episode_number: The episode number
            _step_number: The step number
        """
        self.timestamp = _timestamp
        self.agent_identifier = _agent_identifier
        self.episode_number = _episode_number
        self.step_number = _step_number

    def set_obs_space_pre(self, _obs_space_pre):
        """
        Sets the observation space (pre).

        Args:
            _obs_space_pre: The observation space before any actions are taken
        """
        self.obs_space_pre = _obs_space_pre

    def set_obs_space_post(self, _obs_space_post):
        """
        Sets the observation space (post).

        Args:
            _obs_space_post: The observation space after any actions are taken
        """
        self.obs_space_post = _obs_space_post

    def set_reward(self, _reward):
        """
        Sets the reward.

        Args:
            _reward: The reward value
        """
        self.reward = _reward

    def set_action_space(self, _action_space):
        """
        Sets the action space.

        Args:
            _action_space: The action space invoked by the agent
        """
        self.action_space = _action_space
