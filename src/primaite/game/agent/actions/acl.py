# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import List

from pydantic import field_validator

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat
from primaite.utils.validation.ip_protocol import protocol_validator
from primaite.utils.validation.ipv4_address import ipv4_validator
from primaite.utils.validation.port import port_validator

__all__ = (
    "RouterACLAddRuleAction",
    "RouterACLRemoveRuleAction",
    "FirewallACLAddRuleAction",
    "FirewallACLRemoveRuleAction",
)


class ACLAddRuleAbstractAction(AbstractAction, identifier="acl_add_rule_abstract_action"):
    """Base abstract class for ACL add rule actions."""

    config: ConfigSchema = "ACLAddRuleAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema base for ACL add rule abstract actions."""

        src_ip: IPv4Address
        protocol_name: str
        permission: str
        position: int
        dst_ip: IPv4Address
        src_port: int
        dst_port: int
        src_wildcard: int
        dst_wildcard: int

        @field_validator(
            "src_port",
            "dst_port",
            mode="before",
        )
        @classmethod
        def valid_port(cls, v: str) -> int:
            """Check that inputs are valid."""
            return port_validator(v)

        @field_validator(
            "src_ip",
            "dst_ip",
            mode="before",
        )
        @classmethod
        def valid_ip(cls, v: str) -> str:
            """Check that a valid IP has been provided for src and dst."""
            return ipv4_validator(v)

        @field_validator(
            "protocol_name",
            mode="before",
        )
        @classmethod
        def is_valid_protocol(cls, v: str) -> bool:
            """Check that we are using a valid protocol."""
            return protocol_validator(v)


class ACLRemoveRuleAbstractAction(AbstractAction, identifier="acl_remove_rule_abstract_action"):
    """Base abstract class for ACL remove rule actions."""

    config: ConfigSchema = "ACLRemoveRuleAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema base for ACL remove rule abstract actions."""

        position: int


class RouterACLAddRuleAction(ACLAddRuleAbstractAction, identifier="router_acl_add_rule"):
    """Action which adds a rule to a router's ACL."""

    config: "RouterACLAddRuleAction.ConfigSchema"

    class ConfigSchema(ACLAddRuleAbstractAction.ConfigSchema):
        """Configuration Schema for RouterACLAddRuleAction."""

        target_router: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.target_router,
            "acl",
            "add_rule",
            config.permission,
            config.protocol_name,
            config.src_ip,
            config.src_wildcard,
            config.src_port,
            config.dst_ip,
            config.dst_wildcard,
            config.dst_port,
            config.position,
        ]


class RouterACLRemoveRuleAction(ACLRemoveRuleAbstractAction, identifier="router_acl_remove_rule"):
    """Action which removes a rule from a router's ACL."""

    config: "RouterACLRemoveRuleAction.ConfigSchema"

    class ConfigSchema(ACLRemoveRuleAbstractAction.ConfigSchema):
        """Configuration schema for RouterACLRemoveRuleAction."""

        target_router: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.target_router, "acl", "remove_rule", config.position]


class FirewallACLAddRuleAction(ACLAddRuleAbstractAction, identifier="firewall_acl_add_rule"):
    """Action which adds a rule to a firewall port's ACL."""

    config: "FirewallACLAddRuleAction.ConfigSchema"

    class ConfigSchema(ACLAddRuleAbstractAction.ConfigSchema):
        """Configuration schema for FirewallACLAddRuleAction."""

        target_firewall_nodename: str
        firewall_port_name: str
        firewall_port_direction: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.target_firewall_nodename,
            config.firewall_port_name,
            config.firewall_port_direction,
            "acl",
            "add_rule",
            config.permission,
            config.protocol_name,
            config.src_ip,
            config.src_wildcard,
            config.src_port,
            config.dst_ip,
            config.dst_wildcard,
            config.dst_port,
            config.position,
        ]


class FirewallACLRemoveRuleAction(ACLRemoveRuleAbstractAction, identifier="firewall_acl_remove_rule"):
    """Action which removes a rule from a firewall port's ACL."""

    config: "FirewallACLRemoveRuleAction.ConfigSchema"

    class ConfigSchema(ACLRemoveRuleAbstractAction.ConfigSchema):
        """Configuration schema for FirewallACLRemoveRuleAction."""

        target_firewall_nodename: str
        firewall_port_name: str
        firewall_port_direction: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.target_firewall_nodename,
            config.firewall_port_name,
            config.firewall_port_direction,
            "acl",
            "remove_rule",
            config.position,
        ]
