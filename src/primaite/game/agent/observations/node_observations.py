# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import model_validator

from primaite import getLogger
from primaite.game.agent.observations.firewall_observation import FirewallObservation
from primaite.game.agent.observations.host_observations import HostObservation
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.observations.router_observation import RouterObservation
from primaite.utils.validation.ip_protocol import IPProtocol
from primaite.utils.validation.ipv4_address import StrIP
from primaite.utils.validation.port import Port

_LOGGER = getLogger(__name__)


class NodesObservation(AbstractObservation, discriminator="nodes"):
    """Nodes observation, provides status information about nodes within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NodesObservation."""

        hosts: List[HostObservation.ConfigSchema] = []
        """List of configurations for host observations."""
        routers: List[RouterObservation.ConfigSchema] = []
        """List of configurations for router observations."""
        firewalls: List[FirewallObservation.ConfigSchema] = []
        """List of configurations for firewall observations."""
        num_services: Optional[int] = None
        """Number of services."""
        num_applications: Optional[int] = None
        """Number of applications."""
        num_folders: Optional[int] = None
        """Number of folders."""
        num_files: Optional[int] = None
        """Number of files."""
        num_nics: Optional[int] = None
        """Number of network interface cards (NICs)."""
        include_nmne: Optional[bool] = None
        """Flag to include nmne."""
        monitored_traffic: Optional[Dict[IPProtocol, List[Port]]] = None
        """A dict containing which traffic types are to be included in the observation."""
        include_num_access: Optional[bool] = None
        """Flag to include the number of accesses."""
        file_system_requires_scan: bool = True
        """If True, the folder must be scanned to update the health state. Tf False, the true state is always shown."""
        include_users: Optional[bool] = True
        """If True, report user session information."""
        num_ports: Optional[int] = None
        """Number of ports."""
        ip_list: Optional[List[StrIP]] = None
        """List of IP addresses for encoding ACLs."""
        wildcard_list: Optional[List[str]] = None
        """List of IP wildcards for encoding ACLs."""
        port_list: Optional[List[Port]] = None
        """List of ports for encoding ACLs."""
        protocol_list: Optional[List[IPProtocol]] = None
        """List of protocols for encoding ACLs."""
        num_rules: Optional[int] = None
        """Number of rules ACL rules to show."""

        @model_validator(mode="after")
        def force_optional_fields(self) -> NodesObservation.ConfigSchema:
            """Check that options are specified only if they are needed for the nodes that are part of the config."""
            # check for hosts:
            host_fields = (
                self.num_services,
                self.num_applications,
                self.num_folders,
                self.num_files,
                self.num_nics,
                self.include_nmne,
                self.include_num_access,
            )
            router_fields = (
                self.num_ports,
                self.ip_list,
                self.wildcard_list,
                self.port_list,
                self.protocol_list,
                self.num_rules,
            )
            firewall_fields = (self.ip_list, self.wildcard_list, self.port_list, self.protocol_list, self.num_rules)
            if len(self.hosts) > 0 and any([x is None for x in host_fields]):
                raise ValueError("Configuration error: Host observation options were not fully specified.")
            if len(self.routers) > 0 and any([x is None for x in router_fields]):
                raise ValueError("Configuration error: Router observation options were not fully specified.")
            if len(self.firewalls) > 0 and any([x is None for x in firewall_fields]):
                raise ValueError("Configuration error: Firewall observation options were not fully specified.")
            return self

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
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> NodesObservation:
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
        if not parent_where:
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
            if host_config.monitored_traffic is None:
                host_config.monitored_traffic = config.monitored_traffic
            if host_config.include_num_access is None:
                host_config.include_num_access = config.include_num_access
            if host_config.file_system_requires_scan is None:
                host_config.file_system_requires_scan = config.file_system_requires_scan
            if host_config.include_users is None:
                host_config.include_users = config.include_users

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
            if router_config.include_users is None:
                router_config.include_users = config.include_users

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
            if firewall_config.include_users is None:
                firewall_config.include_users = config.include_users

        hosts = [HostObservation.from_config(config=c, parent_where=where) for c in config.hosts]
        routers = [RouterObservation.from_config(config=c, parent_where=where) for c in config.routers]
        firewalls = [FirewallObservation.from_config(config=c, parent_where=where) for c in config.firewalls]

        return cls(where=where, hosts=hosts, routers=routers, firewalls=firewalls)
