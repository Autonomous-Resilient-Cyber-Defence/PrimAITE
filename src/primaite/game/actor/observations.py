from abc import ABC, abstractmethod
from typing import Any, Dict, Hashable, List

from pydantic import BaseModel

from gym import spaces


def access_from_nested_dict(dictionary: Dict, keys: List[Hashable]) -> Any:
    """
    Access an item from a deeply dictionary with a list of keys.

    For example, if the dictionary is {1: 'a', 2: {3: {4: 'b'}}}, then the key [2, 3, 4] would return 'b', and the key
    [2, 3] would return {4: 'b'}. Raises a KeyError if specified key does not exist at any level of nesting.

    :param dictionary: Deeply nested dictionary
    :type dictionary: Dict
    :param keys: List of dict keys used to traverse the nested dict. Each item corresponds to one level of depth.
    :type keys: List[Hashable]
    :return: The value in the dictionary
    :rtype: Any
    """
    if not keys:
        return dictionary
    k = keys.pop(0)
    try:
        return access_from_nested_dict(dictionary[k], keys)
    except (TypeError, KeyError):
        raise KeyError(f"Cannot find requested key `{k}` in nested dictionary")


class AbstractObservation(BaseModel):

    @abstractmethod
    def __call__(self, state: Dict) -> Any:
        """_summary_

        :param state: _description_
        :type state: Dict
        :return: _description_
        :rtype: Any
        """
        ...
        # receive state dict

    @property
    @abstractmethod
    def space(self) -> spaces.Space:
        """Subclasses must define the shape that they expect"""
        ...


class FileObservation(AbstractObservation):
    where: List[str]
    """Store information about where in the simulation state dictionary to find the relevatn information."""

    def __call__(self, state: Dict) -> Dict:
        file_state = access_from_nested_dict(state, self.where)
        observation = {'health_status':file_state['health_status']}
        return observation

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({'health_status':spaces.Discrete(6)})


class ObservationSpace:
    """Manage the observations of an Actor."""

    ...
    # what this class does:
    # keep a list of observations
    # create observations for an actor from the config


# Example YAML file for agent observation space
"""
arcd_gate:
  rl_framework: SB3
  rl_algo: PPO
  n_learn_steps: 128
  n_learn_episodes: 1000

game_layer:
  agents:
    - ref: client_1_green_user
      type: GREEN
      node_ref: client_1
      service: WebBrowser
      pol:
        - step: 1
          action: START

    - ref: client_1_data_manip_red_bot
      node_ref: client_1
      service: DataManipulationBot
      execution_definition:
        - server_ip_address: 192.168.1.10
        - server_password:
        - payload: 'ATTACK'

      pol:
        - step: 75
          action: EXECUTE




simulation:
  nodes:
    - ref: client_1
      hostname: client_1
      node_type: Computer
      ip_address: 192.168.10.100
      services:
        - name: DataManipulationBot
  links:
    endpoint_a:
    endpoint_b: 1524552-fgfg4147gdh-25gh4gd
rewards:

"""
