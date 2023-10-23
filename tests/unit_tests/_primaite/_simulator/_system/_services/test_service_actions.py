from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


def test_service_scan(service):
    """Test that an agent can request a service scan."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_visible == SoftwareHealthState.UNUSED

    service.apply_request(["scan"])
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_visible == SoftwareHealthState.GOOD


def test_service_stop(service):
    """Test that an agent can request to stop a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["stop"])
    assert service.operating_state == ServiceOperatingState.STOPPED


def test_service_start(service):
    """Test that an agent can request to start a service."""
    assert service.operating_state == ServiceOperatingState.STOPPED
    service.apply_request(["start"])
    assert service.operating_state == ServiceOperatingState.RUNNING


def test_service_pause(service):
    """Test that an agent can request to pause a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["pause"])
    assert service.operating_state == ServiceOperatingState.PAUSED


def test_service_resume(service):
    """Test that an agent can request to resume a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["pause"])
    assert service.operating_state == ServiceOperatingState.PAUSED

    service.apply_request(["resume"])
    assert service.operating_state == ServiceOperatingState.RUNNING


def test_service_restart(service):
    """Test that an agent can request to restart a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["restart"])
    assert service.operating_state == ServiceOperatingState.RESTARTING


def test_service_disable(service):
    """Test that an agent can request to disable a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["disable"])
    assert service.operating_state == ServiceOperatingState.DISABLED


def test_service_enable(service):
    """Test that an agent can request to enable a service."""
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING

    service.apply_request(["disable"])
    assert service.operating_state == ServiceOperatingState.DISABLED

    service.apply_request(["enable"])
    assert service.operating_state == ServiceOperatingState.STOPPED
