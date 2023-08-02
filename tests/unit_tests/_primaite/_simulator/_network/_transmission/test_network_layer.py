import pytest

from primaite.simulator.network.transmission.network_layer import ICMPHeader, ICMPType


def test_icmp_minimal_header_creation():
    """Checks the minimal ICMPHeader (ping 1 request) creation using default values."""
    ping = ICMPHeader()

    assert ping.icmp_type == ICMPType.ECHO_REQUEST
    assert ping.icmp_code == 0
    assert ping.identifier
    assert ping.sequence == 1


def test_valid_icmp_type_code_pairing():
    """Tests ICMPHeader creation with valid type and code pairing."""
    assert ICMPHeader(icmp_type=ICMPType.DESTINATION_UNREACHABLE, icmp_code=6)


def test_invalid_icmp_type_code_pairing():
    """Tests ICMPHeader creation fails with invalid type and code pairing."""
    with pytest.raises(ValueError):
        assert ICMPHeader(icmp_type=ICMPType.DESTINATION_UNREACHABLE, icmp_code=16)
