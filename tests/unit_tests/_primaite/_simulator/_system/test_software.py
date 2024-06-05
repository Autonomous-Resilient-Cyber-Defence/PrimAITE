# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict

import pytest

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.software import IOSoftware, SoftwareHealthState


class TestSoftware(Service):
    def describe_state(self) -> Dict:
        pass


@pytest.fixture(scope="function")
def software(file_system):
    return TestSoftware(
        name="TestSoftware",
        port=Port.ARP,
        file_system=file_system,
        sys_log=SysLog(hostname="test_service"),
        protocol=IPProtocol.TCP,
    )


def test_software_creation(software):
    assert software is not None


def test_software_set_health_state(software):
    assert software.health_state_actual == SoftwareHealthState.UNUSED
    software.set_health_state(SoftwareHealthState.GOOD)
    assert software.health_state_actual == SoftwareHealthState.GOOD
