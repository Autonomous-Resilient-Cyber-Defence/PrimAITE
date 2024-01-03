from uuid import uuid4

from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


def test_scan(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_visible == SoftwareHealthState.UNUSED

    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_visible == SoftwareHealthState.UNUSED

    service.scan()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_visible == SoftwareHealthState.GOOD


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

    timestep = 0
    while service.operating_state == ServiceOperatingState.RESTARTING:
        service.apply_timestep(timestep)
        timestep += 1

    assert service.operating_state == ServiceOperatingState.RUNNING


def test_enable_disable(service):
    service.disable()
    assert service.operating_state == ServiceOperatingState.DISABLED

    service.enable()
    assert service.operating_state == ServiceOperatingState.STOPPED


def test_overwhelm_service(service):
    service.max_sessions = 2
    service.start()

    uuid = str(uuid4())
    assert service.add_connection(connection_id=uuid)  # should be true
    assert service.health_state_actual is SoftwareHealthState.GOOD

    assert not service.add_connection(connection_id=uuid)  # fails because connection already exists
    assert service.health_state_actual is SoftwareHealthState.GOOD

    assert service.add_connection(connection_id=str(uuid4()))  # succeed
    assert service.health_state_actual is SoftwareHealthState.GOOD

    assert not service.add_connection(connection_id=str(uuid4()))  # fail because at capacity
    assert service.health_state_actual is SoftwareHealthState.OVERWHELMED


def test_create_and_remove_connections(service):
    service.start()
    uuid = str(uuid4())

    assert service.add_connection(connection_id=uuid)  # should be true
    assert len(service.connections) == 1
    assert service.health_state_actual is SoftwareHealthState.GOOD

    assert service.remove_connection(connection_id=uuid)  # should be true
    assert len(service.connections) == 0
    assert service.health_state_actual is SoftwareHealthState.GOOD
