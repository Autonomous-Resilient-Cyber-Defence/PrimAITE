# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)


class ACLObservation(AbstractObservation, identifier="ACL"):
    """ACL observation, provides information about access control lists within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ACLObservation."""

        ip_list: Optional[List[IPv4Address]] = None
        """List of IP addresses."""
        wildcard_list: Optional[List[str]] = None
        """List of wildcard strings."""
        port_list: Optional[List[int]] = None
        """List of port numbers."""
        protocol_list: Optional[List[str]] = None
        """List of protocol names."""
        num_rules: Optional[int] = None
        """Number of ACL rules."""

    def __init__(
        self,
        where: WhereType,
        num_rules: int,
        ip_list: List[IPv4Address],
        wildcard_list: List[str],
        port_list: List[int],
        protocol_list: List[str],
    ) -> None:
        """
        Initialise an ACL observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this ACL.
        :type where: WhereType
        :param num_rules: Number of ACL rules.
        :type num_rules: int
        :param ip_list: List of IP addresses.
        :type ip_list: List[IPv4Address]
        :param wildcard_list: List of wildcard strings.
        :type wildcard_list: List[str]
        :param port_list: List of port numbers.
        :type port_list: List[int]
        :param protocol_list: List of protocol names.
        :type protocol_list: List[str]
        """
        self.where = where
        self.num_rules: int = num_rules
        self.ip_to_id: Dict[str, int] = {p: i + 2 for i, p in enumerate(ip_list)}
        self.wildcard_to_id: Dict[str, int] = {p: i + 2 for i, p in enumerate(wildcard_list)}
        self.port_to_id: Dict[int, int] = {p: i + 2 for i, p in enumerate(port_list)}
        self.protocol_to_id: Dict[str, int] = {p: i + 2 for i, p in enumerate(protocol_list)}
        self.default_observation: Dict = {
            i
            + 1: {
                "position": i,
                "permission": 0,
                "source_ip_id": 0,
                "source_wildcard_id": 0,
                "source_port_id": 0,
                "dest_ip_id": 0,
                "dest_wildcard_id": 0,
                "dest_port_id": 0,
                "protocol_id": 0,
            }
            for i in range(self.num_rules)
        }

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing ACL rules.
        :rtype: ObsType
        """
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        obs = {}
        acl_items = dict(acl_state.items())
        i = 1  # don't show rule 0 for compatibility reasons.
        while i < self.num_rules + 1:
            rule_state = acl_items[i]
            if rule_state is None:
                obs[i] = {
                    "position": i - 1,
                    "permission": 0,
                    "source_ip_id": 0,
                    "source_wildcard_id": 0,
                    "source_port_id": 0,
                    "dest_ip_id": 0,
                    "dest_wildcard_id": 0,
                    "dest_port_id": 0,
                    "protocol_id": 0,
                }
            else:
                src_ip = rule_state["src_ip_address"]
                src_node_id = 1 if src_ip is None else self.ip_to_id[src_ip]
                dst_ip = rule_state["dst_ip_address"]
                dst_node_id = 1 if dst_ip is None else self.ip_to_id[dst_ip]
                src_wildcard = rule_state["src_wildcard_mask"]
                src_wildcard_id = self.wildcard_to_id.get(src_wildcard, 1)
                dst_wildcard = rule_state["dst_wildcard_mask"]
                dst_wildcard_id = self.wildcard_to_id.get(dst_wildcard, 1)
                src_port = rule_state["src_port"]
                src_port_id = self.port_to_id.get(src_port, 1)
                dst_port = rule_state["dst_port"]
                dst_port_id = self.port_to_id.get(dst_port, 1)
                protocol = rule_state["protocol"]
                protocol_id = self.protocol_to_id.get(protocol, 1)
                obs[i] = {
                    "position": i - 1,
                    "permission": rule_state["action"],
                    "source_ip_id": src_node_id,
                    "source_wildcard_id": src_wildcard_id,
                    "source_port_id": src_port_id,
                    "dest_ip_id": dst_node_id,
                    "dest_wildcard_id": dst_wildcard_id,
                    "dest_port_id": dst_port_id,
                    "protocol_id": protocol_id,
                }
            i += 1
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for ACL rules.
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
                        "source_ip_id": spaces.Discrete(len(self.ip_to_id) + 2),
                        "source_wildcard_id": spaces.Discrete(len(self.wildcard_to_id) + 2),
                        "source_port_id": spaces.Discrete(len(self.port_to_id) + 2),
                        "dest_ip_id": spaces.Discrete(len(self.ip_to_id) + 2),
                        "dest_wildcard_id": spaces.Discrete(len(self.wildcard_to_id) + 2),
                        "dest_port_id": spaces.Discrete(len(self.port_to_id) + 2),
                        "protocol_id": spaces.Discrete(len(self.protocol_to_id) + 2),
                    }
                )
                for i in range(self.num_rules)
            }
        )

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ACLObservation:
        """
        Create an ACL observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the ACL observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this ACL's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed ACL observation instance.
        :rtype: ACLObservation
        """
        return cls(
            where=parent_where + ["acl", "acl"],
            num_rules=config.num_rules,
            ip_list=config.ip_list,
            wildcard_list=config.wildcard_list,
            port_list=config.port_list,
            protocol_list=config.protocol_list,
        )
