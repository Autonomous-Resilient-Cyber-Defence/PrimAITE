from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class AbstractAction(BaseModel):
    @abstractmethod
    def __call__(self, action: Any) -> List[str]:
        """_summary_

        :param action: _description_
        :type action: Any
        :return: _description_
        :rtype: List[str]
        """
        ...


class ActionSpace:
    ...
