# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""Used to tes the ACL functions."""

from primaite.acl.access_control_list import AccessControlList
from primaite.acl.acl_rule import ACLRule


def test_acl_address_match_1():
    """Test that matching IP addresses produce True."""
    acl = AccessControlList()

    rule = ACLRule("ALLOW", "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


def test_acl_address_match_2():
    """Test that mismatching IP addresses produce False."""
    acl = AccessControlList()

    rule = ACLRule("ALLOW", "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.3") == False


def test_acl_address_match_3():
    """Test the ANY condition for source IP addresses produce True."""
    acl = AccessControlList()

    rule = ACLRule("ALLOW", "ANY", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


def test_acl_address_match_4():
    """Test the ANY condition for dest IP addresses produce True."""
    acl = AccessControlList()

    rule = ACLRule("ALLOW", "192.168.1.1", "ANY", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


def test_check_acl_block_affirmative():
    """Test the block function (affirmative)."""
    # Create the Access Control List
    acl = AccessControlList()

    # Create a rule
    acl_rule_permission = "ALLOW"
    acl_rule_source = "192.168.1.1"
    acl_rule_destination = "192.168.1.2"
    acl_rule_protocol = "TCP"
    acl_rule_port = "80"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
    )

    assert acl.is_blocked("192.168.1.1", "192.168.1.2", "TCP", "80") == False


def test_check_acl_block_negative():
    """Test the block function (negative)."""
    # Create the Access Control List
    acl = AccessControlList()

    # Create a rule
    acl_rule_permission = "DENY"
    acl_rule_source = "192.168.1.1"
    acl_rule_destination = "192.168.1.2"
    acl_rule_protocol = "TCP"
    acl_rule_port = "80"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
    )

    assert acl.is_blocked("192.168.1.1", "192.168.1.2", "TCP", "80") == True


def test_rule_hash():
    """Test the rule hash."""
    # Create the Access Control List
    acl = AccessControlList()

    rule = ACLRule("DENY", "192.168.1.1", "192.168.1.2", "TCP", "80")
    hash_value_local = hash(rule)

    hash_value_remote = acl.get_dictionary_hash("DENY", "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert hash_value_local == hash_value_remote
