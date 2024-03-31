from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.firewall_observation import FirewallObservation
from primaite.game.agent.observations.host_observations import HostObservation
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.observations.router_observation import RouterObservation

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame
_LOGGER = getLogger(__name__)


class NodesObservation(AbstractObservation, identifier="NODES"):
    """Nodes observation, provides status information about nodes within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NodesObservation."""

        hosts: List[HostObservation.ConfigSchema] = []
        """List of configurations for host observations."""
        routers: List[RouterObservation.ConfigSchema] = []
        """List of configurations for router observations."""
        firewalls: List[FirewallObservation.ConfigSchema] = []
        """List of configurations for firewall observations."""
        num_services: int
        """Number of services."""
        num_applications: int
        """Number of applications."""
        num_folders: int
        """Number of folders."""
        num_files: int
        """Number of files."""
        num_nics: int
        """Number of network interface cards (NICs)."""
        include_nmne: bool
        """Flag to include nmne."""
        include_num_access: bool
        """Flag to include the number of accesses."""
        num_ports: int
        """Number of ports."""
        ip_list: List[str]
        """List of IP addresses for encoding ACLs."""
        wildcard_list: List[str]
        """List of IP wildcards for encoding ACLs."""
        port_list: List[int]
        """List of ports for encoding ACLs."""
        protocol_list: List[str]
        """List of protocols for encoding ACLs."""
        num_rules: int
        """Number of rules ACL rules to show."""

    def __init__(
        self,
        where: WhereType,
        hosts: List[HostObservation],
        routers: List[RouterObservation],
        firewalls: List[FirewallObservation],
    ) -> None:
        """
        Initialise a nodes observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for nodes.
            A typical location for nodes might be ['network', 'nodes'].
        :type where: WhereType
        :param hosts: List of host observations.
        :type hosts: List[HostObservation]
        :param routers: List of router observations.
        :type routers: List[RouterObservation]
        :param firewalls: List of firewall observations.
        :type firewalls: List[FirewallObservation]
        """
        self.where: WhereType = where

        self.hosts: List[HostObservation] = hosts
        self.routers: List[RouterObservation] = routers
        self.firewalls: List[FirewallObservation] = firewalls

        self.default_observation = {
            **{f"HOST{i}": host.default_observation for i, host in enumerate(self.hosts)},
            **{f"ROUTER{i}": router.default_observation for i, router in enumerate(self.routers)},
            **{f"FIREWALL{i}": firewall.default_observation for i, firewall in enumerate(self.firewalls)},
        }

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing status information about nodes.
        :rtype: ObsType
        """
        obs = {
            **{f"HOST{i}": host.observe(state) for i, host in enumerate(self.hosts)},
            **{f"ROUTER{i}": router.observe(state) for i, router in enumerate(self.routers)},
            **{f"FIREWALL{i}": firewall.observe(state) for i, firewall in enumerate(self.firewalls)},
        }
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for nodes.
        :rtype: spaces.Space
        """
        space = spaces.Dict(
            {
                **{f"HOST{i}": host.space for i, host in enumerate(self.hosts)},
                **{f"ROUTER{i}": router.space for i, router in enumerate(self.routers)},
                **{f"FIREWALL{i}": firewall.space for i, firewall in enumerate(self.firewalls)},
            }
        )
        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, game: "PrimaiteGame", parent_where: WhereType = []) -> NodesObservation:
        """
        Create a nodes observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for nodes observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about nodes.
            A typical location for nodes might be ['network', 'nodes'].
        :type parent_where: WhereType, optional
        :return: Constructed nodes observation instance.
        :rtype: NodesObservation
        """
        if parent_where is None:
            where = ["network", "nodes"]
        else:
            where = parent_where + ["nodes"]

        for host_config in config.hosts:
            if host_config.num_services is None:
                host_config.num_services = config.num_services
            if host_config.num_applications is None:
                host_config.num_applications = config.num_applications
            if host_config.num_folders is None:
                host_config.num_folders = config.num_folders
            if host_config.num_files is None:
                host_config.num_files = config.num_files
            if host_config.num_nics is None:
                host_config.num_nics = config.num_nics
            if host_config.include_nmne is None:
                host_config.include_nmne = config.include_nmne
            if host_config.include_num_access is None:
                host_config.include_num_access = config.include_num_access

        for router_config in config.routers:
            if router_config.num_ports is None:
                router_config.num_ports = config.num_ports
            if router_config.ip_list is None:
                router_config.ip_list = config.ip_list
            if router_config.wildcard_list is None:
                router_config.wildcard_list = config.wildcard_list
            if router_config.port_list is None:
                router_config.port_list = config.port_list
            if router_config.protocol_list is None:
                router_config.protocol_list = config.protocol_list
            if router_config.num_rules is None:
                router_config.num_rules = config.num_rules

        for firewall_config in config.firewalls:
            if firewall_config.ip_list is None:
                firewall_config.ip_list = config.ip_list
            if firewall_config.wildcard_list is None:
                firewall_config.wildcard_list = config.wildcard_list
            if firewall_config.port_list is None:
                firewall_config.port_list = config.port_list
            if firewall_config.protocol_list is None:
                firewall_config.protocol_list = config.protocol_list
            if firewall_config.num_rules is None:
                firewall_config.num_rules = config.num_rules

        hosts = [HostObservation.from_config(config=c, game=game, parent_where=where) for c in config.hosts]
        routers = [RouterObservation.from_config(config=c, game=game, parent_where=where) for c in config.routers]
        firewalls = [FirewallObservation.from_config(config=c, game=game, parent_where=where) for c in config.firewalls]

        return cls(where=where, hosts=hosts, routers=routers, firewalls=firewalls)
