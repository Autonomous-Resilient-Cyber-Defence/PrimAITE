from abc import ABC, abstractmethod
from typing import Any, Dict, List

class AbstractReward():
    def __init__(self):
        ...

    @abstractmethod
    def calculate(self, state:Dict) -> float:
        return 0.3

class DummyReward(AbstractReward):

    def calculate(self, state: Dict) -> float:
        return -0.1

class RewardFunction():
    __rew_class_identifiers:Dict[str,type[AbstractReward]] = {
        "DUMMY" : DummyReward
    }
    def __init__(self, reward_function:AbstractReward):
        self.reward: AbstractReward = reward_function

    def calculate(self, state:Dict) -> float:
        return self.reward.calculate(state)

    @classmethod
    def from_config(cls, cfg:Dict) -> "RewardFunction":
        for rew_component_cfg in cfg['reward_components']:
            rew_type = rew_component_cfg['type']
            rew_component = cls.__rew_class_identifiers[rew_type]()
            new = cls(reward_function=rew_component)
        return new

