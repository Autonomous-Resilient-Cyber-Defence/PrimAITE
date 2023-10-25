# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Used to tes the ACL functions."""

# from primaite.acl.access_control_list import AccessControlList
# from primaite.acl.acl_rule import ACLRule
# from primaite.common.enums import RulePermissionType


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_acl_address_match_1():
    """Test that matching IP addresses produce True."""
    acl = AccessControlList(RulePermissionType.DENY, 10)

    rule = ACLRule(RulePermissionType.ALLOW, "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_acl_address_match_2():
    """Test that mismatching IP addresses produce False."""
    acl = AccessControlList(RulePermissionType.DENY, 10)

    rule = ACLRule(RulePermissionType.ALLOW, "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.3") == False


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_acl_address_match_3():
    """Test the ANY condition for source IP addresses produce True."""
    acl = AccessControlList(RulePermissionType.DENY, 10)

    rule = ACLRule(RulePermissionType.ALLOW, "ANY", "192.168.1.2", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_acl_address_match_4():
    """Test the ANY condition for dest IP addresses produce True."""
    acl = AccessControlList(RulePermissionType.DENY, 10)

    rule = ACLRule(RulePermissionType.ALLOW, "192.168.1.1", "ANY", "TCP", "80")

    assert acl.check_address_match(rule, "192.168.1.1", "192.168.1.2") == True


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_check_acl_block_affirmative():
    """Test the block function (affirmative)."""
    # Create the Access Control List
    acl = AccessControlList(RulePermissionType.DENY, 10)

    # Create a rule
    acl_rule_permission = RulePermissionType.ALLOW
    acl_rule_source = "192.168.1.1"
    acl_rule_destination = "192.168.1.2"
    acl_rule_protocol = "TCP"
    acl_rule_port = "80"
    acl_position_in_list = "0"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
        acl_position_in_list,
    )
    assert acl.is_blocked("192.168.1.1", "192.168.1.2", "TCP", "80") == False


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_check_acl_block_negative():
    """Test the block function (negative)."""
    # Create the Access Control List
    acl = AccessControlList(RulePermissionType.DENY, 10)

    # Create a rule
    acl_rule_permission = RulePermissionType.DENY
    acl_rule_source = "192.168.1.1"
    acl_rule_destination = "192.168.1.2"
    acl_rule_protocol = "TCP"
    acl_rule_port = "80"
    acl_position_in_list = "0"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
        acl_position_in_list,
    )

    assert acl.is_blocked("192.168.1.1", "192.168.1.2", "TCP", "80") == True


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_rule_hash():
    """Test the rule hash."""
    # Create the Access Control List
    acl = AccessControlList(RulePermissionType.DENY, 10)

    rule = ACLRule(RulePermissionType.DENY, "192.168.1.1", "192.168.1.2", "TCP", "80")
    hash_value_local = hash(rule)

    hash_value_remote = acl.get_dictionary_hash(RulePermissionType.DENY, "192.168.1.1", "192.168.1.2", "TCP", "80")

    assert hash_value_local == hash_value_remote


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
def test_delete_rule():
    """Adds 3 rules and deletes 1 rule and checks its deletion."""
    # Create the Access Control List
    acl = AccessControlList(RulePermissionType.ALLOW, 10)

    # Create a first rule
    acl_rule_permission = RulePermissionType.DENY
    acl_rule_source = "192.168.1.1"
    acl_rule_destination = "192.168.1.2"
    acl_rule_protocol = "TCP"
    acl_rule_port = "80"
    acl_position_in_list = "0"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
        acl_position_in_list,
    )

    # Create a second rule
    acl_rule_permission = RulePermissionType.DENY
    acl_rule_source = "20"
    acl_rule_destination = "30"
    acl_rule_protocol = "FTP"
    acl_rule_port = "21"
    acl_position_in_list = "2"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
        acl_position_in_list,
    )

    # Create a third rule
    acl_rule_permission = RulePermissionType.ALLOW
    acl_rule_source = "192.168.1.3"
    acl_rule_destination = "192.168.1.1"
    acl_rule_protocol = "UDP"
    acl_rule_port = "60"
    acl_position_in_list = "4"

    acl.add_rule(
        acl_rule_permission,
        acl_rule_source,
        acl_rule_destination,
        acl_rule_protocol,
        acl_rule_port,
        acl_position_in_list,
    )
    # Remove the second ACL rule added from the list
    acl.remove_rule(RulePermissionType.DENY, "20", "30", "FTP", "21")

    assert len(acl.acl) == 10
    assert acl.acl[2] is None
