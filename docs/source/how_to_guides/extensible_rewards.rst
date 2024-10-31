.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

Extensible Rewards
******************

Changes to reward class structure.
==================================

Reward classes are inherited from AbstractReward (a sub-class of Pydantic's BaseModel).
Within the reward class is a ConfigSchema class responsible for ensuring config file data is in the
correct format. The `.from_config()` method is generally unchanged.

Inheriting from `BaseModel` removes the need for an `__init__` method bu means that object
attributes need to be passed by keyword.

.. code:: Python

class AbstractReward(BaseModel):
    """Base class for reward function components."""

    class ConfigSchema(BaseModel, ABC):
        """Config schema for AbstractReward."""

        type: str

    _registry: ClassVar[Dict[str, Type["AbstractReward"]]] = {}

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Duplicate node adder {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    def from_config(cls, config: Dict) -> "AbstractReward":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: dict
        :return: The reward component.
        :rtype: AbstractReward
        """
        if config["type"] not in cls._registry:
            raise ValueError(f"Invalid reward type {config['type']}")
        adder_class = cls._registry[config["type"]]
        adder_class.add_nodes_to_net(config=adder_class.ConfigSchema(**config))
        return cls

    @abstractmethod
    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        return 0.0


Changes to YAML file.
=====================
.. code:: YAML

    There's no longer a need to provide a `dns_server` as an option in the simulation section
    of the config file.