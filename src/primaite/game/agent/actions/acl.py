# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from primaite.game.agent.actions.manager import AbstractAction, ActionManager
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


class RouterACLAddRuleAction(AbstractAction, identifier="router_acl_add_rule"):
    """Action which adds a rule to a router's ACL."""

    target_router: str
    position: int
    permission: Literal[1, 2]
    src_ip: str
    source_wildcard_id: int
    source_port: str
    dst_ip: str
    dst_wildcard: int
    dst_port: int
    protocol_name: str

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
        protocol_name: str

    class ACLRuleOptions(BaseModel):
        """Validator for ACL_ADD_RULE options."""

        target_router: str
        """On which router to add the rule, must be specified."""
        position: int
        """At what position to add the rule, must be specified."""
        permission: Literal[1, 2]
        """Whether to allow or deny traffic, must be specified. 1 = PERMIT, 2 = DENY."""
        src_ip: str
        """Rule source IP address. By default, all ip addresses."""
        source_wildcard_id: int = Field(default=0, ge=0)
        """Rule source IP wildcard. By default, use the wildcard at index 0 from action manager."""
        source_port: int = Field(default=1, ge=1)
        """Rule source port. By default, all source ports."""
        dst_ip_id: int = Field(default=1, ge=1)
        """Rule destination IP address. By default, all ip addresses."""
        dst_wildcard: int = Field(default=0, ge=0)
        """Rule destination IP wildcard. By default, use the wildcard at index 0 from action manager."""
        dst_port_id: int = Field(default=1, ge=1)
        """Rule destination port. By default, all destination ports."""
        protocol_name: str = "ALL"
        """Rule protocol. By default, all protocols."""

    #     @field_validator(
    #         "source_ip_id",
    #         "source_port_id",
    #         "source_wildcard_id",
    #         "dest_ip_id",
    #         "dest_port_id",
    #         "dest_wildcard_id",
    #         "protocol_name",
    #         mode="before",
    #     )
    # @classmethod
    # def not_none(cls, v: str, info: ValidationInfo) -> int:
    #     """If None is passed, use the default value instead."""
    #     if v is None:
    #         return cls.model_fields[info.field_name].default
    #     return v

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        # Validate incoming data.
        # parsed_options = RouterACLAddRuleAction.ACLRuleOptions(
        #     target_router=config.target_router,
        #     position=config.position,
        #     permission=config.permission,
        #     src_ip=config.src_ip,
        #     source_wildcard_id=config.source_wildcard_id,
        #     dst_ip_id=config.dst_ip,
        #     dst_wildcard=config.dst_wildcard,
        #     source_port_id=config.source_port_id,
        #     dest_port=config.dst_port,
        #     protocol=config.protocol_name,
        # )

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
            str(config.dst_ip),
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

    def __init__(
        self,
        manager: "ActionManager",
        max_acl_rules: int,
        num_ips: int,
        num_ports: int,
        num_protocols: int,
        **kwargs,
    ) -> None:
        """Init method for FirewallACLAddRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        :param num_ips: Number of IP addresses in the simulation.
        :type num_ips: int
        :param num_ports: Number of ports in the simulation.
        :type num_ports: int
        :param num_protocols: Number of protocols in the simulation.
        :type num_protocols: int
        """
        super().__init__(manager=manager)
        num_permissions = 3
        self.shape: Dict[str, int] = {
            "position": max_acl_rules,
            "permission": num_permissions,
            "source_ip_id": num_ips,
            "dest_ip_id": num_ips,
            "source_port_id": num_ports,
            "dest_port_id": num_ports,
            "protocol_id": num_protocols,
        }

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.permission == 0:
            permission_str = "UNUSED"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        elif config.permission == 1:
            permission_str = "PERMIT"
        elif config.permission == 2:
            permission_str = "DENY"
        # else:
        #     _LOGGER.warning(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if config.protocol_id == 0:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS

        if config.protocol_id == 1:
            protocol = "ALL"
        else:
            # protocol = self.manager.get_internet_protocol_by_idx(protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.
            pass

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

        if config.dest_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif config.dest_ip_id == 1:
            dst_ip = "ALL"
        else:
            # dst_ip = self.manager.get_ip_address_by_idx(dest_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
            pass

        if config.dest_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif config.dest_port_id == 1:
            dst_port = "ALL"
        else:
            # dst_port = self.manager.get_port_by_idx(dest_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
            # src_wildcard = self.manager.get_wildcard_by_idx(source_wildcard_id)
            # dst_wildcard = self.manager.get_wildcard_by_idx(dest_wildcard_id)
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
            protocol,
            str(src_ip),
            config.src_wildcard,
            src_port,
            str(dst_ip),
            config.dst_wildcard,
            dst_port,
            config.position,
        ]


class FirewallACLRemoveRuleAction(AbstractAction, identifier="firewall_acl_remove_rule"):
    """Action which removes a rule from a firewall port's ACL."""

    def __init__(self, manager: "ActionManager", max_acl_rules: int, **kwargs) -> None:
        """Init method for RouterACLRemoveRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"position": max_acl_rules}

    @classmethod
    def form_request(
        cls, target_firewall_nodename: str, firewall_port_name: str, firewall_port_direction: str, position: int
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            target_firewall_nodename,
            firewall_port_name,
            firewall_port_direction,
            "acl",
            "remove_rule",
            position,
        ]
