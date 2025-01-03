# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Dict

import pytest

from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.software import IOSoftware, SoftwareHealthState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


class TestSoftware(Service):
    def describe_state(self) -> Dict:
        pass


@pytest.fixture(scope="function")
def software(file_system):
    return TestSoftware(
        name="TestSoftware",
        port=PORT_LOOKUP["ARP"],
        file_system=file_system,
        sys_log=SysLog(hostname="test_service"),
        protocol=PROTOCOL_LOOKUP["TCP"],
    )


def test_software_creation(software):
    assert software is not None


def test_software_set_health_state(software):
    assert software.health_state_actual == SoftwareHealthState.UNUSED
    software.set_health_state(SoftwareHealthState.GOOD)
    assert software.health_state_actual == SoftwareHealthState.GOOD
