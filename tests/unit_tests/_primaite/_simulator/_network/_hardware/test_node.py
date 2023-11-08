import re
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import Node


def test_node_creation():
    node = Node(hostname="host_1")
