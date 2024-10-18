# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from primaite.game.agent.actions.manager import AbstractAction
from primaite.game.game import _LOGGER
from primaite.interface.request import RequestFormat


class RouterACLAddRuleAction(AbstractAction, identifier="router_acl_add_rule"):
    """Action which adds a rule to a router's ACL."""

    class ACLRuleOptions(BaseModel):
        """Validator for ACL_ADD_RULE options."""

        target_router: str
        """On which router to add the rule, must be specified."""
        position: int
        """At what position to add the rule, must be specified."""
        permission: Literal[1, 2]
        """Whether to allow or deny traffic, must be specified. 1 = PERMIT, 2 = DENY."""
        source_ip_id: int = Field(default=1, ge=1)
        """Rule source IP address. By default, all ip addresses."""
        source_wildcard_id: int = Field(default=0, ge=0)
        """Rule source IP wildcard. By default, use the wildcard at index 0 from action manager."""
        source_port_id: int = Field(default=1, ge=1)
        """Rule source port. By default, all source ports."""
        dest_ip_id: int = Field(default=1, ge=1)
        """Rule destination IP address. By default, all ip addresses."""
        dest_wildcard_id: int = Field(default=0, ge=0)
        """Rule destination IP wildcard. By default, use the wildcard at index 0 from action manager."""
        dest_port_id: int = Field(default=1, ge=1)
        """Rule destination port. By default, all destination ports."""
        protocol_id: int = Field(default=1, ge=1)
        """Rule protocol. By default, all protocols."""

        @field_validator(
            "source_ip_id",
            "source_port_id",
            "source_wildcard_id",
            "dest_ip_id",
            "dest_port_id",
            "dest_wildcard_id",
            "protocol_id",
            mode="before",
        )
        @classmethod
        def not_none(cls, v: str, info: ValidationInfo) -> int:
            """If None is passed, use the default value instead."""
            if v is None:
                return cls.model_fields[info.field_name].default
            return v

    def __init__(
        self,
        manager: "ActionManager",
        max_acl_rules: int,
        num_ips: int,
        num_ports: int,
        num_protocols: int,
        **kwargs,
    ) -> None:
        """Init method for RouterACLAddRuleAction.

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

    def form_request(
        self,
        target_router: str,
        position: int,
        permission: int,
        source_ip_id: int,
        source_wildcard_id: int,
        dest_ip_id: int,
        dest_wildcard_id: int,
        source_port_id: int,
        dest_port_id: int,
        protocol_id: int,
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        # Validate incoming data.
        parsed_options = RouterACLAddRuleAction.ACLRuleOptions(
            target_router=target_router,
            position=position,
            permission=permission,
            source_ip_id=source_ip_id,
            source_wildcard_id=source_wildcard_id,
            dest_ip_id=dest_ip_id,
            dest_wildcard_id=dest_wildcard_id,
            source_port_id=source_port_id,
            dest_port_id=dest_port_id,
            protocol_id=protocol_id,
        )
        if parsed_options.permission == 1:
            permission_str = "PERMIT"
        elif parsed_options.permission == 2:
            permission_str = "DENY"
        else:
            _LOGGER.warning(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if parsed_options.protocol_id == 1:
            protocol = "ALL"
        else:
            protocol = self.manager.get_internet_protocol_by_idx(parsed_options.protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.

        if parsed_options.source_ip_id == 1:
            src_ip = "ALL"
        else:
            src_ip = self.manager.get_ip_address_by_idx(parsed_options.source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        src_wildcard = self.manager.get_wildcard_by_idx(parsed_options.source_wildcard_id)

        if parsed_options.source_port_id == 1:
            src_port = "ALL"
        else:
            src_port = self.manager.get_port_by_idx(parsed_options.source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if parsed_options.dest_ip_id == 1:
            dst_ip = "ALL"
        else:
            dst_ip = self.manager.get_ip_address_by_idx(parsed_options.dest_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
        dst_wildcard = self.manager.get_wildcard_by_idx(parsed_options.dest_wildcard_id)

        if parsed_options.dest_port_id == 1:
            dst_port = "ALL"
        else:
            dst_port = self.manager.get_port_by_idx(parsed_options.dest_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        return [
            "network",
            "node",
            target_router,
            "acl",
            "add_rule",
            permission_str,
            protocol,
            str(src_ip),
            src_wildcard,
            src_port,
            str(dst_ip),
            dst_wildcard,
            dst_port,
            position,
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


class FirewallACLAddRuleAction(AbstractAction, identifier="firewall_acl_add_rule"):
    """Action which adds a rule to a firewall port's ACL."""

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

    def form_request(
        self,
        target_firewall_nodename: str,
        firewall_port_name: str,
        firewall_port_direction: str,
        position: int,
        permission: int,
        source_ip_id: int,
        source_wildcard_id: int,
        dest_ip_id: int,
        dest_wildcard_id: int,
        source_port_id: int,
        dest_port_id: int,
        protocol_id: int,
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if permission == 0:
            permission_str = "UNUSED"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        elif permission == 1:
            permission_str = "PERMIT"
        elif permission == 2:
            permission_str = "DENY"
        else:
            _LOGGER.warning(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if protocol_id == 0:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS

        if protocol_id == 1:
            protocol = "ALL"
        else:
            protocol = self.manager.get_internet_protocol_by_idx(protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.

        if source_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif source_ip_id == 1:
            src_ip = "ALL"
        else:
            src_ip = self.manager.get_ip_address_by_idx(source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if source_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif source_port_id == 1:
            src_port = "ALL"
        else:
            src_port = self.manager.get_port_by_idx(source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif dest_ip_id == 1:
            dst_ip = "ALL"
        else:
            dst_ip = self.manager.get_ip_address_by_idx(dest_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif dest_port_id == 1:
            dst_port = "ALL"
        else:
            dst_port = self.manager.get_port_by_idx(dest_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
        src_wildcard = self.manager.get_wildcard_by_idx(source_wildcard_id)
        dst_wildcard = self.manager.get_wildcard_by_idx(dest_wildcard_id)

        return [
            "network",
            "node",
            target_firewall_nodename,
            firewall_port_name,
            firewall_port_direction,
            "acl",
            "add_rule",
            permission_str,
            protocol,
            str(src_ip),
            src_wildcard,
            src_port,
            str(dst_ip),
            dst_wildcard,
            dst_port,
            position,
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
