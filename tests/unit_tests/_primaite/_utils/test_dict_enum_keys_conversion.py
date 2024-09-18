# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.utils.converters import convert_dict_enum_keys_to_enum_values


def test_simple_conversion():
    """
    Test conversion of a simple dictionary with enum keys to enum values.

    The original dictionary contains one level of nested dictionary with enums as keys.
    The expected output should have string values of enums as keys.
    """
    original_dict = {IPProtocol["UDP"]: {Port["ARP"]: {"inbound": 0, "outbound": 1016.0}}}
    expected_dict = {"udp": {219: {"inbound": 0, "outbound": 1016.0}}}
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict


def test_no_enums():
    """
    Test conversion of a dictionary with no enum keys.

    The original dictionary contains only string keys.
    The expected output should be identical to the original dictionary.
    """
    original_dict = {"protocol": {"port": {"inbound": 0, "outbound": 1016.0}}}
    expected_dict = {"protocol": {"port": {"inbound": 0, "outbound": 1016.0}}}
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict


def test_mixed_keys():
    """
    Test conversion of a dictionary with a mix of enum and string keys.

    The original dictionary contains both enums and strings as keys.
    The expected output should have string values of enums and original string keys.
    """
    original_dict = {
        IPProtocol["TCP"]: {"port": {"inbound": 0, "outbound": 1016.0}},
        "protocol": {Port["HTTP"]: {"inbound": 10, "outbound": 2020.0}},
    }
    expected_dict = {
        "tcp": {"port": {"inbound": 0, "outbound": 1016.0}},
        "protocol": {80: {"inbound": 10, "outbound": 2020.0}},
    }
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict


def test_empty_dict():
    """
    Test conversion of an empty dictionary.

    The original dictionary is empty.
    The expected output should also be an empty dictionary.
    """
    original_dict = {}
    expected_dict = {}
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict


def test_nested_dicts():
    """
    Test conversion of a nested dictionary with multiple levels of nested dictionaries and enums as keys.

    The original dictionary contains nested dictionaries with enums as keys at different levels.
    The expected output should have string values of enums as keys at all levels.
    """
    original_dict = {
        IPProtocol["UDP"]: {Port["ARP"]: {"inbound": 0, "outbound": 1016.0, "details": {IPProtocol["TCP"]: {"latency": "low"}}}}
    }
    expected_dict = {"udp": {219: {"inbound": 0, "outbound": 1016.0, "details": {"tcp": {"latency": "low"}}}}}
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict


def test_non_dict_values():
    """
    Test conversion of a dictionary where some values are not dictionaries.

    The original dictionary contains lists and tuples as values.
    The expected output should preserve these non-dictionary values while converting enum keys to string values.
    """
    original_dict = {IPProtocol["UDP"]: [Port["ARP"], Port["HTTP"]], "protocols": (IPProtocol["TCP"], IPProtocol["UDP"])}
    expected_dict = {"udp": [Port["ARP"], Port["HTTP"]], "protocols": (IPProtocol["TCP"], IPProtocol["UDP"])}
    assert convert_dict_enum_keys_to_enum_values(original_dict) == expected_dict
