from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class AbstractReward(BaseModel):
    def __call__(self, states: List[Dict]) -> float:
        """_summary_

        :param state: _description_
        :type state: Dict
        :return: _description_
        :rtype: float
        """
        ...


class RewardFunction(BaseModel):
    ...
