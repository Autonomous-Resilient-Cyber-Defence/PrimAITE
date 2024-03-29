"""Manages the observation space for the agent."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Type

from gymnasium import spaces
from pydantic import BaseModel, ConfigDict

from primaite import getLogger

_LOGGER = getLogger(__name__)

WhereType = Iterable[str | int] | None


class AbstractObservation(ABC):
    """Abstract class for an observation space component."""

    class ConfigSchema(ABC, BaseModel):
        """Config schema for observations."""

        model_config = ConfigDict(extra="forbid")

    _registry: Dict[str, Type["AbstractObservation"]] = {}
    """Registry of observation components, with their name as key.

    Automatically populated when subclasses are defined. Used for defining from_config.
    """

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        """
        Register an observation type.

        :param identifier: Identifier used to uniquely specify observation component types.
        :type identifier: str
        :raises ValueError: When attempting to create a component with a name that is already in use.
        """
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Duplicate observation component type {identifier}")
        cls._registry[identifier] = cls

    @abstractmethod
    def observe(self, state: Dict) -> Any:
        """
        Return an observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Any
        """
        pass

    @property
    @abstractmethod
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space."""
        pass

    @classmethod
    def from_config(cls, cfg: Dict) -> "AbstractObservation":
        """Create this observation space component form a serialised format."""
        ObservationType = cls._registry[cfg["type"]]
        return ObservationType.from_config(cfg=cfg)


'''
class LinkObservation(AbstractObservation):
    """Observation of a link in the network."""

    default_observation: spaces.Space = {"PROTOCOLS": {"ALL": 0}}
    "Default observation is what should be returned when the link doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise link observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_hostname>,'servics', <service_name>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

        link_state = access_from_nested_dict(state, self.where)
        if link_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        bandwidth = link_state["bandwidth"]
        load = link_state["current_load"]
        if load == 0:
            utilisation_category = 0
        else:
            utilisation_fraction = load / bandwidth
            # 0 is UNUSED, 1 is 0%-10%. 2 is 10%-20%. 3 is 20%-30%. And so on... 10 is exactly 100%
            utilisation_category = int(utilisation_fraction * 9) + 1

        # TODO: once the links support separte load per protocol, this needs amendment to reflect that.
        return {"PROTOCOLS": {"ALL": min(utilisation_category, 10)}}

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict({"PROTOCOLS": spaces.Dict({"ALL": spaces.Discrete(11)})})

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "LinkObservation":
        """Create link observation from a config.

        :param config: Dictionary containing the configuration for this link observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Constructed link observation
        :rtype: LinkObservation
        """
        return cls(where=["network", "links", game.ref_map_links[config["link_ref"]]])


class AclObservation(AbstractObservation):
    """Observation of an Access Control List (ACL) in the network."""

    # TODO: should where be optional, and we can use where=None to pad the observation space?
    # definitely the current approach does not support tracking files that aren't specified by name, for example
    # if a file is created at runtime, we have currently got no way of telling the observation space to track it.
    # this needs adding, but not for the MVP.
    def __init__(
        self,
        node_ip_to_id: Dict[str, int],
        ports: List[int],
        protocols: List[str],
        where: Optional[Tuple[str]] = None,
        num_rules: int = 10,
    ) -> None:
        """Initialise ACL observation.

        :param node_ip_to_id: Mapping between IP address and ID.
        :type node_ip_to_id: Dict[str, int]
        :param ports: List of ports which are part of the game that define the ordering when converting to an ID
        :type ports: List[int]
        :param protocols: List of protocols which are part of the game, defines ordering when converting to an ID
        :type protocols: list[str]
        :param where: Where in the simulation state dictionary to find the relevant information for this ACL. A typical
            example may look like this:
            ['network','nodes',<router_hostname>,'acl','acl']
        :type where: Optional[Tuple[str]], optional
        :param num_rules: , defaults to 10
        :type num_rules: int, optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where
        self.num_rules: int = num_rules
        self.node_to_id: Dict[str, int] = node_ip_to_id
        "List of node IP addresses, order in this list determines how they are converted to an ID"
        self.port_to_id: Dict[int, int] = {port: i + 2 for i, port in enumerate(ports)}
        "List of ports which are part of the game that define the ordering when converting to an ID"
        self.protocol_to_id: Dict[str, int] = {protocol: i + 2 for i, protocol in enumerate(protocols)}
        "List of protocols which are part of the game, defines ordering when converting to an ID"
        self.default_observation: Dict = {
            i
            + 1: {
                "position": i,
                "permission": 0,
                "source_node_id": 0,
                "source_port": 0,
                "dest_node_id": 0,
                "dest_port": 0,
                "protocol": 0,
            }
            for i in range(self.num_rules)
        }

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        # TODO: what if the ACL has more rules than num of max rules for obs space
        obs = {}
        acl_items = dict(acl_state.items())
        i = 1  # don't show rule 0 for compatibility reasons.
        while i < self.num_rules + 1:
            rule_state = acl_items[i]
            if rule_state is None:
                obs[i] = {
                    "position": i - 1,
                    "permission": 0,
                    "source_node_id": 0,
                    "source_port": 0,
                    "dest_node_id": 0,
                    "dest_port": 0,
                    "protocol": 0,
                }
            else:
                src_ip = rule_state["src_ip_address"]
                src_node_id = 1 if src_ip is None else self.node_to_id[IPv4Address(src_ip)]
                dst_ip = rule_state["dst_ip_address"]
                dst_node_ip = 1 if dst_ip is None else self.node_to_id[IPv4Address(dst_ip)]
                src_port = rule_state["src_port"]
                src_port_id = 1 if src_port is None else self.port_to_id[src_port]
                dst_port = rule_state["dst_port"]
                dst_port_id = 1 if dst_port is None else self.port_to_id[dst_port]
                protocol = rule_state["protocol"]
                protocol_id = 1 if protocol is None else self.protocol_to_id[protocol]
                obs[i] = {
                    "position": i - 1,
                    "permission": rule_state["action"],
                    "source_node_id": src_node_id,
                    "source_port": src_port_id,
                    "dest_node_id": dst_node_ip,
                    "dest_port": dst_port_id,
                    "protocol": protocol_id,
                }
            i += 1
        return obs

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                i
                + 1: spaces.Dict(
                    {
                        "position": spaces.Discrete(self.num_rules),
                        "permission": spaces.Discrete(3),
                        # adding two to lengths is to account for reserved values 0 (unused) and 1 (any)
                        "source_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                        "source_port": spaces.Discrete(len(self.port_to_id) + 2),
                        "dest_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                        "dest_port": spaces.Discrete(len(self.port_to_id) + 2),
                        "protocol": spaces.Discrete(len(self.protocol_to_id) + 2),
                    }
                )
                for i in range(self.num_rules)
            }
        )

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "AclObservation":
        """Generate ACL observation from a config.

        :param config: Dictionary containing the configuration for this ACL observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Observation object
        :rtype: AclObservation
        """
        max_acl_rules = config["options"]["max_acl_rules"]
        node_ip_to_idx = {}
        for ip_idx, ip_map_config in enumerate(config["ip_address_order"]):
            node_ref = ip_map_config["node_hostname"]
            nic_num = ip_map_config["nic_num"]
            node_obj = game.simulation.network.nodes[game.ref_map_nodes[node_ref]]
            nic_obj = node_obj.network_interface[nic_num]
            node_ip_to_idx[nic_obj.ip_address] = ip_idx + 2

        router_hostname = config["router_hostname"]
        return cls(
            node_ip_to_id=node_ip_to_idx,
            ports=game.options.ports,
            protocols=game.options.protocols,
            where=["network", "nodes", router_hostname, "acl", "acl"],
            num_rules=max_acl_rules,
        )


class NullObservation(AbstractObservation):
    """Null observation, returns a single 0 value for the observation space."""

    def __init__(self, where: Optional[List[str]] = None):
        """Initialise null observation."""
        self.default_observation: Dict = {}

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation."""
        return 0

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Discrete(1)

    @classmethod
    def from_config(cls, config: Dict, game: Optional["PrimaiteGame"] = None) -> "NullObservation":
        """
        Create null observation from a config.

        The parameters are ignored, they are here to match the signature of the other observation classes.
        """
        return cls()


class ICSObservation(NullObservation):
    """ICS observation placeholder, currently not implemented so always returns a single 0."""

    pass
'''
