from abc import ABC, abstractmethod
from typing import Any, Dict, List

class AbstractReward():
    def __init__(self):
        ...

    def calculate(self, state:Dict) -> float:
        return 0.3


class RewardFunction():
    def __init__(self, reward_function:AbstractReward):
        self.reward: AbstractReward = reward_function

    def calculate(self, state:Dict) -> float:
        return self.reward.calculate(state)
