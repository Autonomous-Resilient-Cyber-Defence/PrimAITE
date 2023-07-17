# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""A class that implements the access control list implementation for the network."""
from typing import Dict

from primaite.acl.acl_rule import ACLRule


class AccessControlList:
    """Access Control List class."""

    def __init__(self):
        """Initialise an empty AccessControlList."""
        self.acl: Dict[str, ACLRule] = {}  # A dictionary of ACL Rules

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
        for rule_key, rule_value in self.acl.items():
            if self.check_address_match(rule_value, _source_ip_address, _dest_ip_address):
                if (rule_value.get_protocol() == _protocol or rule_value.get_protocol() == "ANY") and (
                    str(rule_value.get_port()) == str(_port) or rule_value.get_port() == "ANY"
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
        new_rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
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
        rule = ACLRule(_permission, _source_ip, _dest_ip, _protocol, str(_port))
        hash_value = hash(rule)
        # There will not always be something 'popable' since the agent will be trying random things
        try:
            self.acl.pop(hash_value)
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

    def get_relevant_rules(self, _source_ip_address, _dest_ip_address, _protocol, _port):
        """Get all ACL rules that relate to the given arguments.

        :param _source_ip_address: the source IP address to check
        :param _dest_ip_address: the destination IP address to check
        :param _protocol: the protocol to check
        :param _port: the port to check
        :return: Dictionary of all ACL rules that relate to the given arguments
        :rtype: Dict[str, ACLRule]
        """
        relevant_rules = {}

        for rule_key, rule_value in self.acl.items():
            if self.check_address_match(rule_value, _source_ip_address, _dest_ip_address):
                if (
                    rule_value.get_protocol() == _protocol or rule_value.get_protocol() == "ANY" or _protocol == "ANY"
                ) and (
                    str(rule_value.get_port()) == str(_port) or rule_value.get_port() == "ANY" or str(_port) == "ANY"
                ):
                    # There's a matching rule.
                    relevant_rules[rule_key] = rule_value

        return relevant_rules
