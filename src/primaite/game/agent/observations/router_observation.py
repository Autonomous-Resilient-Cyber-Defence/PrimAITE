# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.acl_observation import ACLObservation
from primaite.game.agent.observations.nic_observations import PortObservation
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)


class RouterObservation(AbstractObservation, identifier="ROUTER"):
    """Router observation, provides status information about a router within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for RouterObservation."""

        hostname: str
        """Hostname of the router, used for querying simulation state dictionary."""
        ports: Optional[List[PortObservation.ConfigSchema]] = None
        """Configuration of port observations for this router."""
        num_ports: Optional[int] = None
        """Number of port observations configured for this router."""
        acl: Optional[ACLObservation.ConfigSchema] = None
        """Configuration of ACL observation on this router."""
        ip_list: Optional[List[str]] = None
        """List of IP addresses for encoding ACLs."""
        wildcard_list: Optional[List[str]] = None
        """List of IP wildcards for encoding ACLs."""
        port_list: Optional[List[int]] = None
        """List of ports for encoding ACLs."""
        protocol_list: Optional[List[str]] = None
        """List of protocols for encoding ACLs."""
        num_rules: Optional[int] = None
        """Number of rules ACL rules to show."""
        include_users: Optional[bool] = True
        """If True, report user session information."""

    def __init__(
        self,
        where: WhereType,
        ports: List[PortObservation],
        num_ports: int,
        acl: ACLObservation,
        include_users: bool,
    ) -> None:
        """
        Initialise a router observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this router.
            A typical location for a router might be ['network', 'nodes', <node_hostname>].
        :type where: WhereType
        :param ports: List of port observations representing the ports of the router.
        :type ports: List[PortObservation]
        :param num_ports: Number of ports for the router.
        :type num_ports: int
        :param acl: ACL observation representing the access control list of the router.
        :type acl: ACLObservation
        :param include_users: If True, report user session information.
        :type include_users: bool
        """
        self.where: WhereType = where
        self.ports: List[PortObservation] = ports
        self.acl: ACLObservation = acl
        self.num_ports: int = num_ports
        self.include_users: bool = include_users
        self.max_users: int = 3
        """Maximum number of remote sessions observable, excess sessions are truncated."""
        while len(self.ports) < num_ports:
            self.ports.append(PortObservation(where=None))
        while len(self.ports) > num_ports:
            self.ports.pop()
            msg = "Too many ports in router observation. Truncating."
            _LOGGER.warning(msg)

        self.default_observation = {
            "ACL": self.acl.default_observation,
        }
        if self.ports:
            self.default_observation["PORTS"] = {i + 1: p.default_observation for i, p in enumerate(self.ports)}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of ports and ACL configuration of the router.
        :rtype: ObsType
        """
        router_state = access_from_nested_dict(state, self.where)
        if router_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["ACL"] = self.acl.observe(state)
        if self.ports:
            obs["PORTS"] = {i + 1: p.observe(state) for i, p in enumerate(self.ports)}
        if self.include_users:
            sess = router_state["services"]["UserSessionManager"]
            obs["users"] = {
                "local_login": 1 if sess["current_local_user"] else 0,
                "remote_sessions": min(self.max_users, len(sess["active_remote_sessions"])),
            }
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for router status.
        :rtype: spaces.Space
        """
        shape = {"ACL": self.acl.space}
        if self.ports:
            shape["PORTS"] = spaces.Dict({i + 1: p.space for i, p in enumerate(self.ports)})
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> RouterObservation:
        """
        Create a router observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the router observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this router's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed router observation instance.
        :rtype: RouterObservation
        """
        where = parent_where + [config.hostname]

        if config.acl is None:
            config.acl = ACLObservation.ConfigSchema()
        if config.acl.num_rules is None:
            config.acl.num_rules = config.num_rules
        if config.acl.ip_list is None:
            config.acl.ip_list = config.ip_list
        if config.acl.wildcard_list is None:
            config.acl.wildcard_list = config.wildcard_list
        if config.acl.port_list is None:
            config.acl.port_list = config.port_list
        if config.acl.protocol_list is None:
            config.acl.protocol_list = config.protocol_list

        if config.ports is None:
            config.ports = [PortObservation.ConfigSchema(port_id=i + 1) for i in range(config.num_ports)]

        ports = [PortObservation.from_config(config=c, parent_where=where) for c in config.ports]
        acl = ACLObservation.from_config(config=config.acl, parent_where=where)
        return cls(where=where, ports=ports, num_ports=config.num_ports, acl=acl, include_users=config.include_users)
