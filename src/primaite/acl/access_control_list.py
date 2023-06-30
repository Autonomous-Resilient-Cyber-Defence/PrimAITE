# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""A class that implements the access control list implementation for the network."""
from typing import Dict

from primaite.acl.acl_rule import ACLRule


class AccessControlList:
    """Access Control List class."""

    def __init__(self):
        """Init."""
        self.acl: Dict[
            str, AccessControlList
        ] = {}  # A dictionary of ACL Rules

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
            or (
                _rule.get_source_ip() == "ANY" and _rule.get_dest_ip() == "ANY"
            )
        ):
            return True
        else:
            return False

    def is_blocked(
        self, _source_ip_address, _dest_ip_address, _protocol, _port
    ):
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
        for rule_key, rule_value in self.acl.items():
            if self.check_address_match(
                rule_value, _source_ip_address, _dest_ip_address
            ):
                if (
                    rule_value.get_protocol() == _protocol
                    or rule_value.get_protocol() == "ANY"
                ) and (
                    str(rule_value.get_port()) == str(_port)
                    or rule_value.get_port() == "ANY"
                ):
                    # There's a matching rule. Get the permission
                    if rule_value.get_permission() == "DENY":
                        return True
                    elif rule_value.get_permission() == "ALLOW":
                        return False

        # If there has been no rule to allow the IER through, it will return a blocked signal by default
        return True

    def add_rule(self, _permission, _source_ip, _dest_ip, _protocol, _port):
        """
        Adds a new rule.

        Args:
            _permission: the permission value (e.g. "ALLOW" or "DENY")
            _source_ip: the source IP address
            _dest_ip: the destination IP address
            _protocol: the protocol
            _port: the port
        """
        new_rule = ACLRule(
            _permission, _source_ip, _dest_ip, _protocol, str(_port)
        )
        hash_value = hash(new_rule)
        self.acl[hash_value] = new_rule

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
        rule = ACLRule(
            _permission, _source_ip, _dest_ip, _protocol, str(_port)
        )
        hash_value = hash(rule)
        # There will not always be something 'popable' since the agent will be trying random things
        try:
            self.acl.pop(hash_value)
        except Exception:
            return

    def remove_all_rules(self):
        """Removes all rules."""
        self.acl.clear()

    def get_dictionary_hash(
        self, _permission, _source_ip, _dest_ip, _protocol, _port
    ):
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
        rule = ACLRule(
            _permission, _source_ip, _dest_ip, _protocol, str(_port)
        )
        hash_value = hash(rule)
        return hash_value
