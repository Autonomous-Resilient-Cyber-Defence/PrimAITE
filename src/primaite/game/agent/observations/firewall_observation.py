# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
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


class FirewallObservation(AbstractObservation, identifier="FIREWALL"):
    """Firewall observation, provides status information about a firewall within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for FirewallObservation."""

        hostname: str
        """Hostname of the firewall node, used for querying simulation state dictionary."""
        ip_list: Optional[List[str]] = None
        """List of IP addresses for encoding ACLs."""
        wildcard_list: Optional[List[str]] = None
        """List of IP wildcards for encoding ACLs."""
        port_list: Optional[List[str]] = None
        """List of ports for encoding ACLs."""
        protocol_list: Optional[List[str]] = None
        """List of protocols for encoding ACLs."""
        num_rules: Optional[int] = None
        """Number of rules ACL rules to show."""
        include_users: Optional[bool] = None
        """If True, report user session information."""

    def __init__(
        self,
        where: WhereType,
        ip_list: List[str],
        wildcard_list: List[str],
        port_list: List[str],
        protocol_list: List[str],
        num_rules: int,
        include_users: bool,
    ) -> None:
        """
        Initialise a firewall observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this firewall.
            A typical location for a firewall might be ['network', 'nodes', <firewall_hostname>].
        :type where: WhereType
        :param ip_list: List of IP addresses.
        :type ip_list: List[str]
        :param wildcard_list: List of wildcard rules.
        :type wildcard_list: List[str]
        :param port_list: List of port names.
        :type port_list: List[str]
        :param protocol_list: List of protocol types.
        :type protocol_list: List[str]
        :param num_rules: Number of rules configured in the firewall.
        :type num_rules: int
        :param include_users: If True, report user session information.
        :type include_users: bool
        """
        self.where: WhereType = where
        self.include_users: bool = include_users
        self.max_users: int = 3
        """Maximum number of remote sessions observable, excess sessions are truncated."""
        self.ports: List[PortObservation] = [
            PortObservation(where=self.where + ["NICs", port_num]) for port_num in (1, 2, 3)
        ]
        # TODO: check what the port nums are for firewall.

        self.internal_inbound_acl = ACLObservation(
            where=self.where + ["internal_inbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.internal_outbound_acl = ACLObservation(
            where=self.where + ["internal_outbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.dmz_inbound_acl = ACLObservation(
            where=self.where + ["dmz_inbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.dmz_outbound_acl = ACLObservation(
            where=self.where + ["dmz_outbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.external_inbound_acl = ACLObservation(
            where=self.where + ["external_inbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.external_outbound_acl = ACLObservation(
            where=self.where + ["external_outbound_acl", "acl"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )

        self.default_observation = {
            "PORTS": {i + 1: p.default_observation for i, p in enumerate(self.ports)},
            "ACL": {
                "INTERNAL": {
                    "INBOUND": self.internal_inbound_acl.default_observation,
                    "OUTBOUND": self.internal_outbound_acl.default_observation,
                },
                "DMZ": {
                    "INBOUND": self.dmz_inbound_acl.default_observation,
                    "OUTBOUND": self.dmz_outbound_acl.default_observation,
                },
                "EXTERNAL": {
                    "INBOUND": self.external_inbound_acl.default_observation,
                    "OUTBOUND": self.external_outbound_acl.default_observation,
                },
            },
        }
        if self.include_users:
            self.default_observation["users"] = {"local_login": 0, "remote_sessions": 0}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of ports and ACLs for internal, DMZ, and external traffic.
        :rtype: ObsType
        """
        firewall_state = access_from_nested_dict(state, self.where)
        if firewall_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        is_on = firewall_state["operating_state"] == 1
        if not is_on:
            obs = {**self.default_observation}

        else:
            obs = {
                "PORTS": {i + 1: p.observe(state) for i, p in enumerate(self.ports)},
                "ACL": {
                    "INTERNAL": {
                        "INBOUND": self.internal_inbound_acl.observe(state),
                        "OUTBOUND": self.internal_outbound_acl.observe(state),
                    },
                    "DMZ": {
                        "INBOUND": self.dmz_inbound_acl.observe(state),
                        "OUTBOUND": self.dmz_outbound_acl.observe(state),
                    },
                    "EXTERNAL": {
                        "INBOUND": self.external_inbound_acl.observe(state),
                        "OUTBOUND": self.external_outbound_acl.observe(state),
                    },
                },
            }
            if self.include_users:
                sess = firewall_state["services"]["UserSessionManager"]
                obs["users"] = {
                    "local_login": 1 if sess["current_local_user"] else 0,
                    "remote_sessions": min(self.max_users, len(sess["active_remote_sessions"])),
                }
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for firewall status.
        :rtype: spaces.Space
        """
        shape = {
            "PORTS": spaces.Dict({i + 1: p.space for i, p in enumerate(self.ports)}),
            "ACL": spaces.Dict(
                {
                    "INTERNAL": spaces.Dict(
                        {
                            "INBOUND": self.internal_inbound_acl.space,
                            "OUTBOUND": self.internal_outbound_acl.space,
                        }
                    ),
                    "DMZ": spaces.Dict(
                        {
                            "INBOUND": self.dmz_inbound_acl.space,
                            "OUTBOUND": self.dmz_outbound_acl.space,
                        }
                    ),
                    "EXTERNAL": spaces.Dict(
                        {
                            "INBOUND": self.external_inbound_acl.space,
                            "OUTBOUND": self.external_outbound_acl.space,
                        }
                    ),
                }
            ),
        }
        if self.include_users:
            shape["users"] = spaces.Dict(
                {"local_login": spaces.Discrete(2), "remote_sessions": spaces.Discrete(self.max_users + 1)}
            )
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> FirewallObservation:
        """
        Create a firewall observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the firewall observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this firewall's
            parent node. A typical location for a node might be ['network', 'nodes', <firewall_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed firewall observation instance.
        :rtype: FirewallObservation
        """
        return cls(
            where=parent_where + [config.hostname],
            ip_list=config.ip_list,
            wildcard_list=config.wildcard_list,
            port_list=config.port_list,
            protocol_list=config.protocol_list,
            num_rules=config.num_rules,
            include_users=config.include_users,
        )
