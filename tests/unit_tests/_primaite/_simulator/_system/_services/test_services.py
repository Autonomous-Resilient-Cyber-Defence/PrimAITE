from typing import Any

import pytest

from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service, ServiceOperatingState


class TestService(Service):
    """Test Service class"""

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        pass


@pytest.fixture(scope="function")
def service(file_system) -> TestService:
    return TestService(
        name="TestService", port=Port.ARP, file_system=file_system, sys_log=SysLog(hostname="test_service")
    )


def test_scan(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.visible_operating_state == ServiceOperatingState.STOPPED

    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.visible_operating_state == ServiceOperatingState.STOPPED

    service.scan()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.visible_operating_state == ServiceOperatingState.RUNNING


def test_start_service(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    service.start()

    assert service.operating_state == ServiceOperatingState.RUNNING


def test_stop_service(service):
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.stop()
    assert service.operating_state == ServiceOperatingState.STOPPED


def test_pause_and_resume_service(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    service.resume()
    assert service.operating_state == ServiceOperatingState.STOPPED

    service.start()
    service.pause()
    assert service.operating_state == ServiceOperatingState.PAUSED

    service.resume()
    assert service.operating_state == ServiceOperatingState.RUNNING


def test_restart(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    service.restart()
    assert service.operating_state == ServiceOperatingState.STOPPED

    service.start()
    service.restart()
    assert service.operating_state == ServiceOperatingState.RESTARTING


def test_enable_disable(service):
    service.disable()
    assert service.operating_state == ServiceOperatingState.DISABLED

    service.enable()
    assert service.operating_state == ServiceOperatingState.STOPPED
