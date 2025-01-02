# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.simulator.network.utils import convert_bytes_to_megabits, convert_megabits_to_bytes


def test_convert_bytes_to_megabits():
    assert round(convert_bytes_to_megabits(B=131072), 5) == float(1)
    assert round(convert_bytes_to_megabits(B=69420), 5) == float(0.52963)


def test_convert_megabits_to_bytes():
    assert round(convert_megabits_to_bytes(Mbits=1), 5) == float(131072)
    assert round(convert_megabits_to_bytes(Mbits=float(0.52963)), 5) == float(69419.66336)
