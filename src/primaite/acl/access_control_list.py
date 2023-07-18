# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""A class that implements the access control list implementation for the network."""
import logging
from typing import Dict, Final, List, Union

from primaite.acl.acl_rule import ACLRule
from primaite.common.enums import RulePermissionType

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class AccessControlList:
    """Access Control List class."""

    def __init__(self, implicit_permission: RulePermissionType, max_acl_rules: int) -> None:
        """Init."""
        # Implicit ALLOW or DENY firewall spec
        self.acl_implicit_permission = implicit_permission
        # Implicit rule in ACL list
        if self.acl_implicit_permission == RulePermissionType.DENY:
            self.acl_implicit_rule = ACLRule(RulePermissionType.DENY, "ANY", "ANY", "ANY", "ANY")
        elif self.acl_implicit_permission == RulePermissionType.ALLOW:
            self.acl_implicit_rule = ACLRule(RulePermissionType.ALLOW, "ANY", "ANY", "ANY", "ANY")
        else:
            raise ValueError(f"implicit permission must be ALLOW or DENY, got {self.acl_implicit_permission}")

        # Maximum number of ACL Rules in ACL
        self.max_acl_rules: int = max_acl_rules
        # A list of ACL Rules
        self._acl: List[Union[ACLRule, None]] = [None] * (self.max_acl_rules - 1)

    @property
    def acl(self) -> List[Union[ACLRule, None]]:
        """Public access method for private _acl."""
        return self._acl + [self.acl_implicit_rule]

    def check_address_match(self, _rule: ACLRule, _source_ip_address: str, _dest_ip_address: str) -> bool:
        """Checks for IP address matches.

        :param _rule: The rule object to check
        :type _rule: ACLRule
        :param _source_ip_address: Source IP address to compare
        :type _source_ip_address: str
        :param _dest_ip_address: Destination IP address to compare
        :type _dest_ip_address: str
        :return: True if there is a match, otherwise False.
        :rtype: bool
        """
        if (
            (_rule.get_source_ip() == _source_ip_address and _rule.get_dest_ip() == _dest_ip_address)
            or (_rule.get_source_ip() == "ANY" and _rule.get_dest_ip() == _dest_ip_address)
            or (_rule.get_source_ip() == _source_ip_address and _rule.get_dest_ip() == "ANY")
            or (_rule.get_source_ip() == "ANY" and _rule.get_dest_ip() == "ANY")
        ):
            return True
        else:
            return False

    def is_blocked(self, _source_ip_address: str, _dest_ip_address: str, _protocol: str, _port: str) -> bool:
        """
        Checks for rules that block a protocol / port.

        Args:
            _source_ip_address: the source IP address to check
            _dest_ip_address: the destination IP address to check
            _protocol: the protocol to check
            _port: the port to check

        Returns:
             Indicates block if all conditions are satisfied.
        """
        for rule in self.acl:
            if isinstance(rule, ACLRule):
                if self.check_address_match(rule, _source_ip_address, _dest_ip_address):
                    if (rule.get_protocol() == _protocol or rule.get_protocol() == "ANY") and (
                        str(rule.get_port()) == str(_port) or rule.get_port() == "ANY"
                    ):
                        # There's a matching rule. Get the permission
                        if rule.get_permission() == RulePermissionType.DENY:
                            return True
                        elif rule.get_permission() == RulePermissionType.ALLOW:
                            return False

        # If there has been no rule to allow the IER through, it will return a blocked signal by default
        return True

    def add_rule(
        self, _permission: str, _source_ip: str, _dest_ip: str, _protocol: str, _port: str, _position: int
    ) -> None:
        """
        Adds a new rule.

        Args:
            _permission: the permission value (e.g. "ALLOW" or "DENY")
            _source_ip: the source IP address
            _dest_ip: the destination IP address
            _protocol: the protocol
            _port: the port
            _position: position to insert ACL rule into ACL list (starting from index 1 and NOT 0)
        """
        try:
            position_index = int(_position)
        except TypeError:
            _LOGGER.info(f"Position {_position} could not be converted to integer.")
            return

        new_rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        # Checks position is in correct range
        if self.max_acl_rules - 1 > position_index > -1:
            try:
                _LOGGER.info(f"Position {position_index} is valid.")
                # Check to see Agent will not overwrite current ACL in ACL list
                if self._acl[position_index] is None:
                    _LOGGER.info(f"Inserting rule {new_rule} at position {position_index}")
                    # Adds rule
                    self._acl[position_index] = new_rule
                else:
                    # Cannot overwrite it
                    _LOGGER.info(f"Error: inserting rule at non-empty position {position_index}")
                    return
            except Exception:
                _LOGGER.info(f"New Rule could NOT be added to list at position {position_index}.")
        else:
            _LOGGER.info(f"Position {position_index} is an invalid/overwrites implicit firewall rule")

    def remove_rule(
        self, _permission: RulePermissionType, _source_ip: str, _dest_ip: str, _protocol: str, _port: str
    ) -> None:
        """
        Removes a rule.

        Args:
            _permission: the permission value (e.g. "ALLOW" or "DENY")
            _source_ip: the source IP address
            _dest_ip: the destination IP address
            _protocol: the protocol
            _port: the port
        """
        rule_to_delete = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        delete_rule_hash = hash(rule_to_delete)

        for index in range(0, len(self._acl)):
            if isinstance(self._acl[index], ACLRule) and hash(self._acl[index]) == delete_rule_hash:
                self._acl[index] = None

    def remove_all_rules(self) -> None:
        """Removes all rules."""
        for i in range(len(self._acl)):
            self._acl[i] = None

    def get_dictionary_hash(self, _permission: str, _source_ip: str, _dest_ip: str, _protocol: str, _port: str) -> int:
        """
        Produces a hash value for a rule.

        Args:
            _permission: the permission value (e.g. "ALLOW" or "DENY")
            _source_ip: the source IP address
            _dest_ip: the destination IP address
            _protocol: the protocol
            _port: the port

        Returns:
             Hash value based on rule parameters.
        """
        rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        hash_value = hash(rule)
        return hash_value

    def get_relevant_rules(
        self, _source_ip_address: str, _dest_ip_address: str, _protocol: str, _port: str
    ) -> Dict[int, ACLRule]:
        """Get all ACL rules that relate to the given arguments.

        :param _source_ip_address: the source IP address to check
        :param _dest_ip_address: the destination IP address to check
        :param _protocol: the protocol to check
        :param _port: the port to check
        :return: Dictionary of all ACL rules that relate to the given arguments
        :rtype: Dict[int, ACLRule]
        """
        relevant_rules = {}
        for rule in self.acl:
            if self.check_address_match(rule, _source_ip_address, _dest_ip_address):
                if (rule.get_protocol() == _protocol or rule.get_protocol() == "ANY" or _protocol == "ANY") and (
                    str(rule.get_port()) == str(_port) or rule.get_port() == "ANY" or str(_port) == "ANY"
                ):
                    # There's a matching rule.
                    relevant_rules[self._acl.index(rule)] = rule

        return relevant_rules
