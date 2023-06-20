"""Module for handling configurable observation spaces in PrimAITE."""
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Final, List, Tuple, Union

import numpy as np
from gym import spaces

from primaite.acl.acl_rule import ACLRule
from primaite.common.enums import (
    FileSystemState,
    HardwareState,
    Protocol,
    RulePermissionType,
    SoftwareState,
)
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.service_node import ServiceNode

# This dependency is only needed for type hints,
# TYPE_CHECKING is False at runtime and True when typecheckers are performing typechecking
# Therefore, this avoids circular dependency problem.
if TYPE_CHECKING:
    from primaite.environment.primaite_env import Primaite

_LOGGER = logging.getLogger(__name__)


class AbstractObservationComponent(ABC):
    """Represents a part of the PrimAITE observation space."""

    @abstractmethod
    def __init__(self, env: "Primaite"):
        _LOGGER.info(f"Initialising {self} observation component")
        self.env: "Primaite" = env
        self.space: spaces.Space
        self.current_observation: np.ndarray  # type might be too restrictive?
        return NotImplemented

    @abstractmethod
    def update(self):
        """Update the observation based on the current state of the environment."""
        self.current_observation = NotImplemented


class NodeLinkTable(AbstractObservationComponent):
    """Table with nodes and links as rows and hardware/software status as cols.

    This will create the observation space formatted as a table of integers.
    There is one row per node, followed by one row per link.
    The number of columns is 4 plus one per service. They are:
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
    """

    _FIXED_PARAMETERS: int = 4
    _MAX_VAL: int = 1_000_000
    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
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
        self.current_observation = np.zeros(observation_shape, dtype=self._DATA_TYPE)

    def update(self):
        """Update the observation based on current environment state.

        The structure of the observation space is described in :class:`.NodeLinkTable`
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
    """Flat list of nodes' hardware, OS, file system, and service states.

    The MultiDiscrete observation space can be though of as a one-dimensional vector of discrete states, represented by
    integers.
    Each node has 3 elements plus 1 per service. It will have the following structure:
    .. code-block::
        [
            node1 hardware state,
            node1 OS state,
            node1 file system state,
            node1 service1 state,
            node1 service2 state,
            node1 serviceN state (one for each service),
            node2 hardware state,
            node2 OS state,
            node2 file system state,
            node2 service1 state,
            node2 service2 state,
            node2 serviceN state (one for each service),
            ...
        ]

    :param env: The environment that forms the basis of the observations
    :type env: Primaite
    """

    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
        super().__init__(env)

        # 1. Define the shape of your observation space component
        node_shape = [
            len(HardwareState) + 1,
            len(SoftwareState) + 1,
            len(FileSystemState) + 1,
        ]
        services_shape = [len(SoftwareState) + 1] * self.env.num_services
        node_shape = node_shape + services_shape

        shape = node_shape * self.env.num_nodes
        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)

        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

    def update(self):
        """Update the observation based on current environment state.

        The structure of the observation space is described in :class:`.NodeStatuses`
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
            obs.extend(
                [hardware_state, software_state, file_system_state, *service_states]
            )
        self.current_observation[:] = obs


class LinkTrafficLevels(AbstractObservationComponent):
    """Flat list of traffic levels encoded into banded categories.

    For each link, total traffic or traffic per service is encoded into a categorical value.
    For example, if ``quantisation_levels=5``, the traffic levels represent these values:
        0 = No traffic (0% of bandwidth)
        1 = No traffic (0%-33% of bandwidth)
        2 = No traffic (33%-66% of bandwidth)
        3 = No traffic (66%-100% of bandwidth)
        4 = No traffic (100% of bandwidth)

    .. note::
        The lowest category always corresponds to no traffic and the highest category to the link being at max capacity.
        Any amount of traffic between 0% and 100% (exclusive) is divided evenly into the remaining categories.

    :param env: The environment that forms the basis of the observations
    :type env: Primaite
    :param combine_service_traffic: Whether to consider total traffic on the link, or each protocol individually,
    defaults to False
    :type combine_service_traffic: bool, optional
    :param quantisation_levels: How many bands to consider when converting the traffic amount to a categorical value ,
    defaults to 5
    :type quantisation_levels: int, optional
    """

    _DATA_TYPE: type = np.int64

    def __init__(
        self,
        env: "Primaite",
        combine_service_traffic: bool = False,
        quantisation_levels: int = 5,
    ):
        if quantisation_levels < 3:
            _msg = (
                f"quantisation_levels must be 3 or more because the lowest and highest levels are "
                f"reserved for 0% and 100% link utilisation, got {quantisation_levels} instead. "
                f"Resetting to default value (5)"
            )
            _LOGGER.warning(_msg)
            quantisation_levels = 5

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

    def update(self):
        """Update the observation based on current environment state.

        The structure of the observation space is described in :class:`.LinkTrafficLevels`
        """
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
                        1 / (self._quantisation_levels - 2)
                    ) + 1

                obs.append(int(traffic_level))

        self.current_observation[:] = obs


class AccessControlList(AbstractObservationComponent):
    """Flat list of all the Access Control Rules in the Access Control List.

    The MultiDiscrete observation space can be though of as a one-dimensional vector of discrete states, represented by
    integers.

    :param env: The environment that forms the basis of the observations
    :type env: Primaite

    Each ACL Rule has 6 elements. It will have the following structure:
    .. code-block::
        [
            acl_rule1 permission,
            acl_rule1 source_ip,
            acl_rule1 dest_ip,
            acl_rule1 protocol,
            acl_rule1 port,
            acl_rule1 position,
            acl_rule2 permission,
            acl_rule2 source_ip,
            acl_rule2 dest_ip,
            acl_rule2 protocol,
            acl_rule2 port,
            acl_rule2 position,
            ...
        ]
    """

    # Terms (for ACL observation space):
    # [0, 1] - Permission (0 = DENY, 1 = ALLOW)
    # [0, num nodes] - Source IP (0 = any, then 1 -> x resolving to IP addresses)
    # [0, num nodes] - Dest IP (0 = any, then 1 -> x resolving to IP addresses)
    # [0, num services] - Protocol (0 = any, then 1 -> x resolving to protocol)
    # [0, num ports] - Port (0 = any, then 1 -> x resolving to port)
    # [0, max acl rules - 1] - Position (0 = first index, then 1 -> x index resolving to acl rule in acl list)

    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
        super().__init__(env)

        # 1. Define the shape of your observation space component
        acl_shape = [
            len(RulePermissionType),
            len(env.nodes) + 1,
            len(env.nodes) + 1,
            len(env.services_list),
            len(env.ports_list),
            env.max_number_acl_rules,
        ]
        len(acl_shape)
        # shape = acl_shape
        shape = acl_shape * self.env.max_number_acl_rules

        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)
        print("obs space:", self.space)
        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

    def update(self):
        """Update the observation based on current environment state.

        The structure of the observation space is described in :class:`.AccessControlList`
        """
        obs = []

        for index in range(len(self.env.acl.acl)):
            acl_rule = self.env.acl.acl[index]
            if isinstance(acl_rule, ACLRule):
                permission = acl_rule.permission
                source_ip = acl_rule.source_ip
                dest_ip = acl_rule.dest_ip
                protocol = acl_rule.protocol
                port = acl_rule.port
                position = index

                source_ip_int = -1
                dest_ip_int = -1
                if permission == "DENY":
                    permission_int = 0
                else:
                    permission_int = 1
                if source_ip == "ANY":
                    source_ip_int = 0
                else:
                    nodes = list(self.env.nodes.values())
                    for node in nodes:
                        # print(node.ip_address, source_ip, node.ip_address == source_ip)
                        if (
                            isinstance(node, ServiceNode)
                            or isinstance(node, ActiveNode)
                        ) and node.ip_address == source_ip:
                            source_ip_int = node.node_id
                            break
                if dest_ip == "ANY":
                    dest_ip_int = 0
                else:
                    nodes = list(self.env.nodes.values())
                    for node in nodes:
                        if (
                            isinstance(node, ServiceNode)
                            or isinstance(node, ActiveNode)
                        ) and node.ip_address == dest_ip:
                            dest_ip_int = node.node_id
                if protocol == "ANY":
                    protocol_int = 0
                else:
                    try:
                        protocol_int = Protocol[protocol].value
                    except AttributeError:
                        _LOGGER.info(f"Service {protocol} could not be found")
                        protocol_int = -1
                if port == "ANY":
                    port_int = 0
                else:
                    if port in self.env.ports_list:
                        port_int = self.env.ports_list.index(port)
                    else:
                        _LOGGER.info(f"Port {port} could not be found.")

                # Either do the multiply on the obs space
                # Change the obs to
                if source_ip_int != -1 and dest_ip_int != -1:
                    items_to_add = [
                        permission_int,
                        source_ip_int,
                        dest_ip_int,
                        protocol_int,
                        port_int,
                        position,
                    ]
                    position = position * 6
                    for item in items_to_add:
                        obs.insert(position, int(item))
                        position += 1
                else:
                    items_to_add = [-1, -1, -1, -1, -1, index]
                    position = index * 6
                    for item in items_to_add:
                        obs.insert(position, int(item))
                        position += 1

        self.current_observation = obs
        print("current observation space:", self.current_observation)


class ObservationsHandler:
    """Component-based observation space handler.

    This allows users to configure observation spaces by mixing and matching components.
    Each component can also define further parameters to make them more flexible.
    """

    _REGISTRY: Final[Dict[str, type]] = {
        "NODE_LINK_TABLE": NodeLinkTable,
        "NODE_STATUSES": NodeStatuses,
        "LINK_TRAFFIC_LEVELS": LinkTrafficLevels,
        "ACCESS_CONTROL_LIST": AccessControlList,
    }

    def __init__(self):
        self.registered_obs_components: List[AbstractObservationComponent] = []
        self.space: spaces.Space
        self.current_observation: Union[Tuple[np.ndarray], np.ndarray]

    def update_obs(self):
        """Fetch fresh information about the environment."""
        current_obs = []
        for obs in self.registered_obs_components:
            obs.update()
            current_obs.append(obs.current_observation)

        # If there is only one component, don't use a tuple, just pass through that component's obs.
        if len(current_obs) == 1:
            self.current_observation = current_obs[0]
        else:
            self.current_observation = tuple(current_obs)
            # TODO: We may need to add ability to flatten the space as not all agents support tuple spaces.

    def register(self, obs_component: AbstractObservationComponent):
        """Add a component for this handler to track.

        :param obs_component: The component to add.
        :type obs_component: AbstractObservationComponent
        """
        self.registered_obs_components.append(obs_component)
        self.update_space()

    def deregister(self, obs_component: AbstractObservationComponent):
        """Remove a component from this handler.

        :param obs_component: Which component to remove. It must exist within this object's
        ``registered_obs_components`` attribute.
        :type obs_component: AbstractObservationComponent
        """
        self.registered_obs_components.remove(obs_component)
        self.update_space()

    def update_space(self):
        """Rebuild the handler's composite observation space from its components."""
        component_spaces = []
        for obs_comp in self.registered_obs_components:
            component_spaces.append(obs_comp.space)

        # If there is only one component, don't use a tuple space, just pass through that component's space.
        if len(component_spaces) == 1:
            self.space = component_spaces[0]
        else:
            self.space = spaces.Tuple(component_spaces)
            # TODO: We may need to add ability to flatten the space as not all agents support tuple spaces.

    @classmethod
    def from_config(cls, env: "Primaite", obs_space_config: dict):
        """Parse a config dictinary, return a new observation handler populated with new observation component objects.

        The expected format for the config dictionary is:

        ..code-block::python
            config = {
                components: [
                    {
                        "name": "<COMPONENT1_NAME>"
                    },
                    {
                        "name": "<COMPONENT2_NAME>"
                        "options": {"opt1": val1, "opt2": val2}
                    },
                    {
                        ...
                    },
                ]
            }

        :return: Observation handler
        :rtype: primaite.environment.observations.ObservationsHandler
        """
        # Instantiate the handler
        handler = cls()

        for component_cfg in obs_space_config["components"]:
            # Figure out which class can instantiate the desired component
            comp_type = component_cfg["name"]
            comp_class = cls._REGISTRY[comp_type]

            # Create the component with options from the YAML
            options = component_cfg.get("options") or {}
            component = comp_class(env, **options)

            handler.register(component)

        handler.update_obs()
        return handler
