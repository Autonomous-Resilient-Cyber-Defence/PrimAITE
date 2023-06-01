"""Module for handling configurable observation spaces in PrimAITE."""
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple

import numpy as np
from gym import spaces

from primaite.common.enums import FileSystemState, HardwareState, SoftwareState
from primaite.environment.primaite_env import Primaite
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.service_node import ServiceNode

_LOGGER = logging.getLogger(__name__)


class AbstractObservationComponent(ABC):
    """Represents a part of the PrimAITE observation space."""

    @abstractmethod
    def __init__(self, env: Primaite):
        _LOGGER.info(f"Initialising {self} observation component")
        self.env: Primaite = env
        self.space: spaces.Space
        self.current_observation: np.ndarray  # type might be too restrictive?
        return NotImplemented

    @abstractmethod
    def update(self):
        """Look at the environment and update the current observation value."""
        self.current_observation = NotImplemented


class NodeLinkTable(AbstractObservationComponent):
    """Table with nodes/links as rows and hardware/software status as cols.

    Initialise the observation space with the BOX option chosen.

    This will create the observation space formatted as a table of integers.
    There is one row per node, followed by one row per link.
    Columns are as follows:
        * node/link ID
        * node hardware status / 0 for links
        * node operating system status (if active/service) / 0 for links
        * node file system status (active/service only) / 0 for links
        * node service1 status / traffic load from that service for links
        * node service2 status / traffic load from that service for links
        * ...
        * node serviceN status / traffic load from that service for links

    For example if the environment has 5 nodes, 7 links, and 3 services, the observation space shape will be
    ``(12, 7)``
    #todo: clean up description

    """

    _FIXED_PARAMETERS = 4
    _MAX_VAL = 1_000_000
    _DATA_TYPE = np.int64

    def __init__(self, env: Primaite):
        super().__init__(env)

        # 1. Define the shape of your observation space component
        num_items = self.env.num_links + self.env.num_nodes
        num_columns = self.env.num_services + self._FIXED_PARAMETERS
        observation_shape = (num_items, num_columns)

        # 2. Create Observation space
        self.space = spaces.Box(
            low=0,
            high=self._MAX_VAL,
            shape=observation_shape,
            dtype=self._DATA_TYPE,
        )

        # 3. Initialise Observation with zeroes
        self.current_observation = np.zeroes(observation_shape, dtype=self._DATA_TYPE)

    def update_obs(self):
        """Update the observation.

        Update the environment's observation state based on the current status of nodes and links.

        The structure of the observation space is described in :func:`~_init_box_observations`
        This function can only be called if the observation space setting is set to BOX.
        todo: complete description..
        """
        item_index = 0
        nodes = self.env.nodes
        links = self.env.links
        # Do nodes first
        for _, node in nodes.items():
            self.current_observation[item_index][0] = int(node.node_id)
            self.current_observation[item_index][1] = node.hardware_state.value
            if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                self.current_observation[item_index][2] = node.software_state.value
                self.current_observation[item_index][
                    3
                ] = node.file_system_state_observed.value
            else:
                self.current_observation[item_index][2] = 0
                self.current_observation[item_index][3] = 0
            service_index = 4
            if isinstance(node, ServiceNode):
                for service in self.env.services_list:
                    if node.has_service(service):
                        self.current_observation[item_index][
                            service_index
                        ] = node.get_service_state(service).value
                    else:
                        self.current_observation[item_index][service_index] = 0
                    service_index += 1
            else:
                # Not a service node
                for service in self.env.services_list:
                    self.current_observation[item_index][service_index] = 0
                    service_index += 1
            item_index += 1

        # Now do links
        for _, link in links.items():
            self.current_observation[item_index][0] = int(link.get_id())
            self.current_observation[item_index][1] = 0
            self.current_observation[item_index][2] = 0
            self.current_observation[item_index][3] = 0
            protocol_list = link.get_protocol_list()
            protocol_index = 0
            for protocol in protocol_list:
                self.current_observation[item_index][
                    protocol_index + 4
                ] = protocol.get_load()
                protocol_index += 1
            item_index += 1


class NodeStatuses(AbstractObservationComponent):
    """todo: complete description.

    This will create the observation space with node observations followed by link observations.
    Each node has 3 elements in the observation space plus 1 per service, more specifically:
        * hardware state
        * operating system state
        * file system state
        * service states (one per service)
    """

    _DATA_TYPE = np.int64

    def __init__(self, env: Primaite):
        super().__init__(env)

        # 1. Define the shape of your observation space component
        shape = [
            len(HardwareState) + 1,
            len(SoftwareState) + 1,
            len(FileSystemState) + 1,
        ]
        services_shape = [len(SoftwareState) + 1] * self.env.num_services
        shape = shape + services_shape

        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)

        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

    def update_obs(self):
        """todo: complete description.

        Update the environment's observation state based on the current status of nodes and links.

        The structure of the observation space is described in :func:`~_init_multidiscrete_observations`
        This function can only be called if the observation space setting is set to MULTIDISCRETE.


        """
        obs = []
        for _, node in self.env.nodes.items():
            hardware_state = node.hardware_state.value
            software_state = 0
            file_system_state = 0
            service_states = [0] * self.env.num_services

            if isinstance(node, ActiveNode):
                software_state = node.software_state.value
                file_system_state = node.file_system_state_observed.value

            if isinstance(node, ServiceNode):
                for i, service in enumerate(self.env.services_list):
                    if node.has_service(service):
                        service_states[i] = node.get_service_state(service).value
        obs.extend([hardware_state, software_state, file_system_state, *service_states])
        self.current_observation[:] = obs


class LinkTrafficLevels(AbstractObservationComponent):
    """todo: complete description.

    Each link has one element in the observation space, corresponding to the traffic load,
    it can take the following values:
        0 = No traffic (0% of bandwidth)
        1 = No traffic (0%-33% of bandwidth)
        2 = No traffic (33%-66% of bandwidth)
        3 = No traffic (66%-100% of bandwidth)
        4 = No traffic (100% of bandwidth)
    """

    _DATA_TYPE = np.int64

    def __init__(
        self,
        env: Primaite,
        combine_service_traffic: bool = False,
        quantisation_levels: int = 5,
    ):
        super().__init__(env)
        self._combine_service_traffic: bool = combine_service_traffic
        self._quantisation_levels: int = quantisation_levels
        self._entries_per_link: int = 1

        if not self._combine_service_traffic:
            self._entries_per_link = self.env.num_services

        # 1. Define the shape of your observation space component
        shape = (
            [self._quantisation_levels] * self.env.num_links * self._entries_per_link
        )

        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)

        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

    def update_obs(self):
        """todo: complete description."""
        obs = []
        for _, link in self.env.links.items():
            bandwidth = link.bandwidth
            if self._combine_service_traffic:
                loads = [link.get_current_load()]
            else:
                loads = [protocol.get_load() for protocol in link.protocol_list]

            for load in loads:
                if load <= 0:
                    traffic_level = 0
                elif load >= bandwidth:
                    traffic_level = self._quantisation_levels - 1
                else:
                    traffic_level = (load / bandwidth) // (
                        1 / (self._quantisation_levels - 1)
                    ) + 1

                obs.append(int(traffic_level))

        self.current_observation[:] = obs


class ObservationsHandler:
    """Component-based observation space handler."""

    class registry(Enum):
        """todo: complete description."""

        NODE_LINK_TABLE: NodeLinkTable
        NODE_STATUSES: NodeStatuses
        LINK_TRAFFIC_LEVELS: LinkTrafficLevels

    def __init__(self):
        """todo: complete description."""
        """Initialise the handler without any components yet. They"""
        self.registered_obs_components: List[AbstractObservationComponent] = []
        self.space: spaces.Space
        self.current_observation: Tuple[np.ndarray]
        # i can access the registry items like this:
        # self.registry.LINK_TRAFFIC_LEVELS

    def update_obs(self):
        """todo: complete description."""
        current_obs = []
        for obs in self.registered_obs_components:
            obs.update_obs()
            current_obs.append(obs.current_observation)
        self.current_observation = tuple(current_obs)

    def register(self, obs_component: AbstractObservationComponent):
        """todo: complete description."""
        self.registered_obs_components.append(obs_component)
        self.update_space()

    def deregister(self, obs_component: AbstractObservationComponent):
        """todo: complete description."""
        self.registered_obs_components.remove(obs_component)
        self.update_space()

    def update_space(self):
        """todo: complete description."""
        component_spaces = []
        for obs_comp in self.registered_obs_components:
            component_spaces.append(obs_comp.space)
        self.space = spaces.Tuple(component_spaces)

    @classmethod
    def from_config(cls, obs_space_config):
        """todo: complete description.

        This method parses config items related to the observation space, then
        creates the necessary components and adds them to the observation handler.
        """
        # Instantiate the handler
        handler = cls()

        for component_cfg in obs_space_config["components"]:
            # Figure out which class can instantiate the desired component
            comp_type = component_cfg["name"]
            comp_class = cls.registry[comp_type].value

            # Create the component with options from the YAML
            component = comp_class(**component_cfg["options"])

            handler.register(component)

        return handler
