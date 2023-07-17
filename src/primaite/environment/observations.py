"""Module for handling configurable observation spaces in PrimAITE."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Final, List, Tuple, TYPE_CHECKING, Union

import numpy as np
from gym import spaces

from primaite.acl.acl_rule import ACLRule
from primaite.common.enums import FileSystemState, HardwareState, RulePermissionType, SoftwareState
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
        """
        Initialise observation component.

        :param env: Primaite training environment.
        :type env: Primaite
        """
        _LOGGER.info(f"Initialising {self} observation component")
        self.env: "Primaite" = env
        self.space: spaces.Space
        self.current_observation: np.ndarray  # type might be too restrictive?
        self.structure: List[str]
        return NotImplemented

    @abstractmethod
    def update(self):
        """Update the observation based on the current state of the environment."""
        self.current_observation = NotImplemented

    @abstractmethod
    def generate_structure(self) -> List[str]:
        """Return a list of labels for the components of the flattened observation space."""
        return NotImplemented


class NodeLinkTable(AbstractObservationComponent):
    """
    Table with nodes and links as rows and hardware/software status as cols.

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
    _MAX_VAL: int = 1_000_000_000
    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
        """
        Initialise a NodeLinkTable observation space component.

        :param env: Training environment.
        :type env: Primaite
        """
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

        self.structure = self.generate_structure()

    def update(self):
        """
        Update the observation based on current environment state.

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
                self.current_observation[item_index][3] = node.file_system_state_observed.value
            else:
                self.current_observation[item_index][2] = 0
                self.current_observation[item_index][3] = 0
            service_index = 4
            if isinstance(node, ServiceNode):
                for service in self.env.services_list:
                    if node.has_service(service):
                        self.current_observation[item_index][service_index] = node.get_service_state(service).value
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
                self.current_observation[item_index][protocol_index + 4] = protocol.get_load()
                protocol_index += 1
            item_index += 1

    def generate_structure(self):
        """Return a list of labels for the components of the flattened observation space."""
        nodes = self.env.nodes.values()
        links = self.env.links.values()

        structure = []

        for i, node in enumerate(nodes):
            node_id = node.node_id
            node_labels = [
                f"node_{node_id}_id",
                f"node_{node_id}_hardware_status",
                f"node_{node_id}_os_status",
                f"node_{node_id}_fs_status",
            ]
            for j, serv in enumerate(self.env.services_list):
                node_labels.append(f"node_{node_id}_service_{serv}_status")

            structure.extend(node_labels)

        for i, link in enumerate(links):
            link_id = link.id
            link_labels = [
                f"link_{link_id}_id",
                f"link_{link_id}_n/a",
                f"link_{link_id}_n/a",
                f"link_{link_id}_n/a",
            ]
            for j, serv in enumerate(self.env.services_list):
                link_labels.append(f"link_{link_id}_service_{serv}_load")

            structure.extend(link_labels)
        return structure


class NodeStatuses(AbstractObservationComponent):
    """
    Flat list of nodes' hardware, OS, file system, and service states.

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
    """

    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
        """
        Initialise a NodeStatuses observation component.

        :param env: Training environment.
        :type env: Primaite
        """
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
        self.structure = self.generate_structure()

    def update(self):
        """
        Update the observation based on current environment state.

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
                [
                    hardware_state,
                    software_state,
                    file_system_state,
                    *service_states,
                ]
            )
        self.current_observation[:] = obs

    def generate_structure(self):
        """Return a list of labels for the components of the flattened observation space."""
        services = self.env.services_list

        structure = []

        for _, node in self.env.nodes.items():
            node_id = node.node_id
            structure.append(f"node_{node_id}_hardware_state_NONE")
            for state in HardwareState:
                structure.append(f"node_{node_id}_hardware_state_{state.name}")
            structure.append(f"node_{node_id}_software_state_NONE")
            for state in SoftwareState:
                structure.append(f"node_{node_id}_software_state_{state.name}")
            structure.append(f"node_{node_id}_file_system_state_NONE")
            for state in FileSystemState:
                structure.append(f"node_{node_id}_file_system_state_{state.name}")
            for service in services:
                structure.append(f"node_{node_id}_service_{service}_state_NONE")
                for state in SoftwareState:
                    structure.append(f"node_{node_id}_service_{service}_state_{state.name}")
        return structure


class LinkTrafficLevels(AbstractObservationComponent):
    """
    Flat list of traffic levels encoded into banded categories.

    For each link, total traffic or traffic per service is encoded into a categorical value.
    For example, if ``quantisation_levels=5``, the traffic levels represent these values:

        * 0 = No traffic (0% of bandwidth)
        * 1 = No traffic (0%-33% of bandwidth)
        * 2 = No traffic (33%-66% of bandwidth)
        * 3 = No traffic (66%-100% of bandwidth)
        * 4 = No traffic (100% of bandwidth)

    .. note::
        The lowest category always corresponds to no traffic and the highest category to the link being at max capacity.
        Any amount of traffic between 0% and 100% (exclusive) is divided evenly into the remaining categories.

    """

    _DATA_TYPE: type = np.int64

    def __init__(
        self,
        env: "Primaite",
        combine_service_traffic: bool = False,
        quantisation_levels: int = 5,
    ):
        """
        Initialise a LinkTrafficLevels observation component.

        :param env: The environment that forms the basis of the observations
        :type env: Primaite
        :param combine_service_traffic: Whether to consider total traffic on the link, or each protocol individually,
            defaults to False
        :type combine_service_traffic: bool, optional
        :param quantisation_levels: How many bands to consider when converting the traffic amount to a categorical
            value, defaults to 5
        :type quantisation_levels: int, optional
        """
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
        shape = [self._quantisation_levels] * self.env.num_links * self._entries_per_link

        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)

        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

        self.structure = self.generate_structure()

    def update(self):
        """
        Update the observation based on current environment state.

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
                    traffic_level = (load / bandwidth) // (1 / (self._quantisation_levels - 2)) + 1

                obs.append(int(traffic_level))

        self.current_observation[:] = obs

    def generate_structure(self):
        """Return a list of labels for the components of the flattened observation space."""
        structure = []
        for _, link in self.env.links.items():
            link_id = link.id
            if self._combine_service_traffic:
                protocols = ["overall"]
            else:
                protocols = [protocol.name for protocol in link.protocol_list]

            for p in protocols:
                for i in range(self._quantisation_levels):
                    structure.append(f"link_{link_id}_{p}_traffic_level_{i}")
        return structure


class AccessControlList(AbstractObservationComponent):
    """Flat list of all the Access Control Rules in the Access Control List.

    The MultiDiscrete observation space can be though of as a one-dimensional vector of discrete states, represented by
    integers.

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


    Terms (for ACL Observation Space):
        [0, 1, 2] - Permission (0 = NA, 1 = DENY, 2 = ALLOW)
        [0, num nodes] - Source IP (0 = NA, 1 = any, then 2 -> x resolving to Node IDs)
        [0, num nodes] - Dest IP (0 = NA, 1 = any, then 2 -> x resolving to Node IDs)
        [0, num services] - Protocol (0 = NA, 1 = any, then 2 -> x resolving to protocol)
        [0, num ports] - Port (0 = NA, 1 = any, then 2 -> x resolving to port)
        [0, max acl rules - 1] - Position (0 = NA, 1 = first index, then 2 -> x index resolving to acl rule in acl list)

    NOTE: NA is Non-Applicable - this means the ACL Rule in the list is a NoneType and NOT an ACLRule object.
    """

    _DATA_TYPE: type = np.int64

    def __init__(self, env: "Primaite"):
        """
        Initialise an AccessControlList observation component.

        :param env: The environment that forms the basis of the observations
        :type env: Primaite
        """
        super().__init__(env)

        # 1. Define the shape of your observation space component
        # The NA and ANY types means that there are 2 extra items for Nodes, Services and Ports.
        # Number of ACL rules incremented by 1 for positions starting at index 0.
        acl_shape = [
            len(RulePermissionType),
            len(env.nodes) + 2,
            len(env.nodes) + 2,
            len(env.services_list) + 2,
            len(env.ports_list) + 2,
            env.max_number_acl_rules,
        ]
        shape = acl_shape * self.env.max_number_acl_rules

        # 2. Create Observation space
        self.space = spaces.MultiDiscrete(shape)

        # 3. Initialise observation with zeroes
        self.current_observation = np.zeros(len(shape), dtype=self._DATA_TYPE)

        self.structure = self.generate_structure()

    def update(self):
        """Update the observation based on current environment state.

        The structure of the observation space is described in :class:`.AccessControlList`
        """
        obs = []

        for index in range(0, len(self.env.acl.acl)):
            acl_rule = self.env.acl.acl[index]
            if isinstance(acl_rule, ACLRule):
                permission = acl_rule.permission
                source_ip = acl_rule.source_ip
                dest_ip = acl_rule.dest_ip
                protocol = acl_rule.protocol
                port = acl_rule.port
                position = index
                # Map each ACL attribute from what it was to an integer to fit the observation space
                source_ip_int = None
                dest_ip_int = None
                if permission == "DENY":
                    permission_int = 1
                else:
                    permission_int = 2
                if source_ip == "ANY":
                    source_ip_int = 1
                else:
                    # Map Node ID (+ 1) to source IP address
                    nodes = list(self.env.nodes.values())
                    for node in nodes:
                        if (
                            isinstance(node, ServiceNode) or isinstance(node, ActiveNode)
                        ) and node.ip_address == source_ip:
                            source_ip_int = int(node.node_id) + 1
                            break
                if dest_ip == "ANY":
                    dest_ip_int = 1
                else:
                    # Map Node ID (+ 1) to dest IP address
                    # Index of Nodes start at 1 so + 1 is needed so NA can be added.
                    nodes = list(self.env.nodes.values())
                    for node in nodes:
                        if (
                            isinstance(node, ServiceNode) or isinstance(node, ActiveNode)
                        ) and node.ip_address == dest_ip:
                            dest_ip_int = int(node.node_id) + 1
                if protocol == "ANY":
                    protocol_int = 1
                else:
                    # Index of protocols and ports start from 0 so + 2 is needed to add NA and ANY
                    try:
                        protocol_int = self.env.services_list.index(protocol) + 2
                    except AttributeError:
                        _LOGGER.info(f"Service {protocol} could not be found")
                        protocol_int = None
                if port == "ANY":
                    port_int = 1
                else:
                    if port in self.env.ports_list:
                        port_int = self.env.ports_list.index(port) + 2
                    else:
                        _LOGGER.info(f"Port {port} could not be found.")
                        port_int = None
                # Add to current obs
                obs.extend(
                    [
                        permission_int,
                        source_ip_int,
                        dest_ip_int,
                        protocol_int,
                        port_int,
                        position,
                    ]
                )

            else:
                # The Nothing or NA representation of 'NONE' ACL rules
                obs.extend([0, 0, 0, 0, 0, 0])

        self.current_observation[:] = obs

    def generate_structure(self):
        """Return a list of labels for the components of the flattened observation space."""
        structure = []
        for acl_rule in self.env.acl.acl:
            acl_rule_id = self.env.acl.acl.index(acl_rule)

            for permission in RulePermissionType:
                structure.append(f"acl_rule_{acl_rule_id}_permission_{permission.name}")

            structure.append(f"acl_rule_{acl_rule_id}_source_ip_ANY")
            for node in self.env.nodes.keys():
                structure.append(f"acl_rule_{acl_rule_id}_source_ip_{node}")

            structure.append(f"acl_rule_{acl_rule_id}_dest_ip_ANY")
            for node in self.env.nodes.keys():
                structure.append(f"acl_rule_{acl_rule_id}_dest_ip_{node}")

            structure.append(f"acl_rule_{acl_rule_id}_service_ANY")
            for service in self.env.services_list:
                structure.append(f"acl_rule_{acl_rule_id}_service_{service}")

            structure.append(f"acl_rule_{acl_rule_id}_port_ANY")
            for port in self.env.ports_list:
                structure.append(f"acl_rule_{acl_rule_id}_port_{port}")

        return structure


class ObservationsHandler:
    """
    Component-based observation space handler.

    This allows users to configure observation spaces by mixing and matching components. Each component can also define
    further parameters to make them more flexible.
    """

    _REGISTRY: Final[Dict[str, type]] = {
        "NODE_LINK_TABLE": NodeLinkTable,
        "NODE_STATUSES": NodeStatuses,
        "LINK_TRAFFIC_LEVELS": LinkTrafficLevels,
        "ACCESS_CONTROL_LIST": AccessControlList,
    }

    def __init__(self):
        """Initialise the observation handler."""
        self.registered_obs_components: List[AbstractObservationComponent] = []

        # internal the observation space (unflattened version of space if flatten=True)
        self._space: spaces.Space
        # flattened version of the observation space
        self._flat_space: spaces.Space

        self._observation: Union[Tuple[np.ndarray], np.ndarray]
        # used for transactions and when flatten=true
        self._flat_observation: np.ndarray

    def update_obs(self):
        """Fetch fresh information about the environment."""
        current_obs = []
        for obs in self.registered_obs_components:
            obs.update()
            current_obs.append(obs.current_observation)

        if len(current_obs) == 1:
            self._observation = current_obs[0]
        else:
            self._observation = tuple(current_obs)
        self._flat_observation = spaces.flatten(self._space, self._observation)

    def register(self, obs_component: AbstractObservationComponent):
        """
        Add a component for this handler to track.

        :param obs_component: The component to add.
        :type obs_component: AbstractObservationComponent
        """
        self.registered_obs_components.append(obs_component)
        self.update_space()

    def deregister(self, obs_component: AbstractObservationComponent):
        """
        Remove a component from this handler.

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

        # if there are multiple components, build a composite tuple space
        if len(component_spaces) == 1:
            self._space = component_spaces[0]
        else:
            self._space = spaces.Tuple(component_spaces)
        if len(component_spaces) > 0:
            self._flat_space = spaces.flatten_space(self._space)
        else:
            self._flat_space = spaces.Box(0, 1, (0,))

    @property
    def space(self):
        """Observation space, return the flattened version if flatten is True."""
        if len(self.registered_obs_components) > 1:
            return self._flat_space
        else:
            return self._space

    @property
    def current_observation(self):
        """Current observation, return the flattened version if flatten is True."""
        if len(self.registered_obs_components) > 1:
            return self._flat_observation
        else:
            return self._observation

    @classmethod
    def from_config(cls, env: "Primaite", obs_space_config: dict):
        """
        Parse a config dictinary, return a new observation handler populated with new observation component objects.

        The expected format for the config dictionary is:

        .. code-block:: python

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

        if obs_space_config.get("flatten"):
            handler.flatten = True

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

    def describe_structure(self):
        """
        Create a list of names for the features of the obs space.

        The order of labels follows the flattened version of the space.
        """
        # as it turns out it's not possible to take the gym flattening function and apply it to our labels so we have
        # to fake it. each component has to just hard-code the expected label order after flattening...

        labels = []
        for obs_comp in self.registered_obs_components:
            labels.extend(obs_comp.structure)

        return labels
