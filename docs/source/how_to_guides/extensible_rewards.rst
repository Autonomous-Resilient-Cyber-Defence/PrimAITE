.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

Extensible Rewards
******************
Extensible Rewards differ from the previous reward mechanism used in PrimAITE v3.x as new reward
types can be added without requiring a change to the RewardFunction class in rewards.py (PrimAITE
core repository).

Changes to reward class structure.
==================================

Reward classes are inherited from AbstractReward (a sub-class of Pydantic's BaseModel).
Within the reward class there is a ConfigSchema class responsible for ensuring the config file data
is in the correct format. This also means there is little (if no) requirement for and `__init__`
method. The `.from_config` method is no longer required as it's inherited from `AbstractReward`.
Each class requires an identifier string which is used by the ConfigSchema class to verify that it
hasn't previously been added to the registry.

Inheriting from `BaseModel` removes the need for an `__init__` method but means that object
attributes need to be passed by keyword.

To add a new reward class follow the example below. Note that the type attribute in the
`ConfigSchema` class should match the type used in the config file to define the reward.

.. code-block:: Python

class DatabaseFileIntegrity(AbstractReward, identifier="DATABASE_FILE_INTEGRITY"):
    """Reward function component which rewards the agent for maintaining the integrity of a database file."""

    config: "DatabaseFileIntegrity.ConfigSchema"
    location_in_state: List[str] = [""]
    reward: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for DatabaseFileIntegrity."""

        type: str = "DATABASE_FILE_INTEGRITY"
        node_hostname: str
        folder_name: str
        file_name: str

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.
        pass



Changes to YAML file.
=====================
.. code:: YAML

    There's no longer a need to provide a `dns_server` as an option in the simulation section
    of the config file.
