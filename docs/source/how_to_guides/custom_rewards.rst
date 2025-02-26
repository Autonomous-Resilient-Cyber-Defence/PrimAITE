.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _custom_rewards:

Creating Custom Rewards in PrimAITE
***********************************

Rewards within PrimAITE are contained within ``rewards.py``, which details the rewards available for all agents within training sessions, how they are calculated and any other specific information where necessary.

Custom Rewards within PrimAITE should inherit from the ``AbstractReward`` class, found in ``rewards.py``. It's important to include an identifier for any class created within PrimAITE.

.. code:: Python

    class ExampleAward(AbstractReward, identifier="ExampleAward"):
        """Example Reward Class """

        def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
            """Calculate the reward for the current state."""
            return 1.0

        @classmethod
        def from_config(cls, config: dict) -> "AbstractReward":
            """Create a reward function component from a config dictionary."""
            return cls()


Custom rewards that have been created should be added to the ``rew_class_identifiers`` dictionary within the ``RewardFunction`` class in ``rewards.py``.

Including Custom Rewards within PrimAITE configuration
======================================================

Custom rewards can then be included within an agents configuration by it's inclusion within the training session configuration YAML.

.. code:: yaml

    agents:
      - ref: agent_name
        reward_function:
          reward_components:
            - type: DUMMY
              weight: 1.0


More detailed information about rewards within PrimAITE can be found within :ref:`Rewards`
