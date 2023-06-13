# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""A class that implements the access control list implementation for the network."""
import logging
from typing import Final, List

from primaite.acl.acl_rule import ACLRule

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class AccessControlList:
    """Access Control List class."""

    def __init__(self, implicit_permission, max_acl_rules):
        """Init."""
        # Implicit ALLOW or DENY firewall spec
        # Last rule in the ACL list
        self.acl_implicit_rule = implicit_permission
        # Create implicit rule based on input
        if self.acl_implicit_rule == "DENY":
            implicit_rule = ACLRule("DENY", "ANY", "ANY", "ANY", "ANY")
        else:
            implicit_rule = ACLRule("ALLOW", "ANY", "ANY", "ANY", "ANY")

        # Maximum number of ACL Rules in ACL
        self.max_acl_rules: int = max_acl_rules
        # A list of ACL Rules
        self.acl: List[ACLRule] = [implicit_rule]

    def check_address_match(self, _rule, _source_ip_address, _dest_ip_address):
        """
        Checks for IP address matches.

        Args:
            _rule: The rule being checked
            _source_ip_address: the source IP address to compare
            _dest_ip_address: the destination IP address to compare

        Returns:
             True if match; False otherwise.
        """
        if (
            (
                _rule.get_source_ip() == _source_ip_address
                and _rule.get_dest_ip() == _dest_ip_address
            )
            or (
                _rule.get_source_ip() == "ANY"
                and _rule.get_dest_ip() == _dest_ip_address
            )
            or (
                _rule.get_source_ip() == _source_ip_address
                and _rule.get_dest_ip() == "ANY"
            )
            or (_rule.get_source_ip() == "ANY" and _rule.get_dest_ip() == "ANY")
        ):
            return True
        else:
            return False

    def is_blocked(self, _source_ip_address, _dest_ip_address, _protocol, _port):
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
            if self.check_address_match(rule, _source_ip_address, _dest_ip_address):
                if (
                    rule.get_protocol() == _protocol or rule.get_protocol() == "ANY"
                ) and (str(rule.get_port()) == str(_port) or rule.get_port() == "ANY"):
                    # There's a matching rule. Get the permission
                    if rule.get_permission() == "DENY":
                        return True
                    elif rule.get_permission() == "ALLOW":
                        return False

        # If there has been no rule to allow the IER through, it will return a blocked signal by default
        return True

    def add_rule(self, _permission, _source_ip, _dest_ip, _protocol, _port, _position):
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
        position_index = int(_position)
        new_rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        if len(self.acl) < self.max_acl_rules:
            if len(self.acl) > position_index > -1:
                try:
                    self.acl.insert(position_index, new_rule)
                except Exception:
                    _LOGGER.info(
                        f"New Rule could NOT be added to list at position {position_index}."
                    )
            else:
                _LOGGER.info(
                    f"Position {position_index} is an invalid index for list and/or overwrites implicit firewall rule"
                )
        else:
            _LOGGER.info(
                f"The ACL list is FULL."
                f"The list of ACLs has length {len(self.acl)} and it has a max capacity of {self.max_acl_rules}."
            )

    def remove_rule(self, _permission, _source_ip, _dest_ip, _protocol, _port):
        """
        Removes a rule.

        Args:
            _permission: the permission value (e.g. "ALLOW" or "DENY")
            _source_ip: the source IP address
            _dest_ip: the destination IP address
            _protocol: the protocol
            _port: the port
        """
        # Add check so you cant remove implicit rule
        rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        # There will not always be something 'popable' since the agent will be trying random things
        try:
            self.acl.remove(rule)
        except Exception:
            return

    def remove_all_rules(self):
        """Removes all rules."""
        self.acl.clear()

    def get_dictionary_hash(self, _permission, _source_ip, _dest_ip, _protocol, _port):
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
