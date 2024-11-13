# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import List, Literal

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "RouterACLAddRuleAction",
    "RouterACLRemoveRuleAction",
    "FirewallACLAddRuleAction",
    "FirewallACLRemoveRuleAction",
)


class ACLAbstractAction(AbstractAction, identifier="acl_abstract_action"):
    """Base class for ACL actions."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema base for ACL abstract actions."""

        src_ip: str
        protocol_name: str


class RouterACLAddRuleAction(AbstractAction, identifier="router_acl_add_rule"):
    """Action which adds a rule to a router's ACL."""

    target_router: str
    position: int
    permission: Literal[1, 2]
    source_wildcard_id: int
    source_port: str
    dst_ip: str
    dst_wildcard: int
    dst_port: int

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema for RouterACLAddRuleAction."""

        target_router: str
        position: int
        permission: Literal[1, 2]
        src_ip: str
        src_wildcard: int
        source_port: str
        dst_ip: str
        dst_wildcard: int
        dst_port: int

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


class RouterACLRemoveRuleAction(AbstractAction, identifier="router_acl_remove_rule"):
    """Action which removes a rule from a router's ACL."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for RouterACLRemoveRuleAction."""

        target_router: str
        position: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.target_router, "acl", "remove_rule", config.position]


class FirewallACLAddRuleAction(ACLAbstractAction, identifier="firewall_acl_add_rule"):
    """Action which adds a rule to a firewall port's ACL."""

    max_acl_rules: int
    num_ips: int
    num_ports: int
    num_protocols: int
    num_permissions: int = 3
    permission: str

    class ConfigSchema(ACLAbstractAction.ConfigSchema):
        """Configuration schema for FirewallACLAddRuleAction."""

        max_acl_rules: int
        num_ips: int
        num_ports: int
        num_protocols: int
        num_permissions: int = 3
        permission: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.protocol_id == 0:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        if config.source_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif config.source_ip_id == 1:
            src_ip = "ALL"
        else:
            # src_ip = self.manager.get_ip_address_by_idx(source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
            pass

        if config.source_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif config.source_port_id == 1:
            src_port = "ALL"
        else:
            # src_port = self.manager.get_port_by_idx(source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
            pass

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
            str(src_ip),
            config.src_wildcard,
            src_port,
            config.dst_ip,
            config.dst_wildcard,
            config.dst_port,
            config.position,
        ]


class FirewallACLRemoveRuleAction(AbstractAction, identifier="firewall_acl_remove_rule"):
    """Action which removes a rule from a firewall port's ACL."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for FirewallACLRemoveRuleAction."""

        target_firewall_nodename: str
        firewall_port_name: str
        firewall_port_direction: str
        position: int

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
