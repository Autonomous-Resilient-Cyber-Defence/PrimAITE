# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import List

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

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

        src_ip: str
        protocol_name: str
        permission: str
        position: int
        src_ip: str
        dst_ip: str
        src_port: str
        dst_port: str
        src_wildcard: int
        dst_wildcard: int


class ACLRemoveRuleAbstractAction(AbstractAction, identifier="acl_remove_rule_abstract_action"):
    """Base abstract class for ACL remove rule actions."""

    config: ConfigSchema = "ACLRemoveRuleAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema base for ACL remove rule abstract actions."""

        src_ip: str
        protocol_name: str
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
            config.source_port,
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
        if config.protocol_name is None:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        if config.src_ip == 0:
            return ["do_nothing"]  # invalid formulation
        if config.src_port == 0:
            return ["do_nothing"]  # invalid configuration.

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
