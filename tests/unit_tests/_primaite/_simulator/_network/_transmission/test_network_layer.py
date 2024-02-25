import pytest

from primaite.simulator.network.protocols.icmp import ICMPPacket, ICMPType


def test_icmp_minimal_header_creation():
    """Checks the minimal ICMPPacket (ping 1 request) creation using default values."""
    ping = ICMPPacket()

    assert ping.icmp_type == ICMPType.ECHO_REQUEST
    assert ping.icmp_code == 0
    assert ping.identifier
    assert ping.sequence == 0


def test_valid_icmp_type_code_pairing():
    """Tests ICMPPacket creation with valid type and code pairing."""
    assert ICMPPacket(icmp_type=ICMPType.DESTINATION_UNREACHABLE, icmp_code=6)


def test_invalid_icmp_type_code_pairing():
    """Tests ICMPPacket creation fails with invalid type and code pairing."""
    with pytest.raises(ValueError):
        assert ICMPPacket(icmp_type=ICMPType.DESTINATION_UNREACHABLE, icmp_code=16)
