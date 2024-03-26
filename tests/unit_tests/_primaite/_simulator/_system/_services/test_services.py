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
    assert service.health_state_actual == SoftwareHealthState.UNUSED
    service.start()

    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.GOOD


def test_stop_service(service):
    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.GOOD

    service.stop()
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_actual == SoftwareHealthState.GOOD


def test_pause_and_resume_service(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    service.resume()
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_actual == SoftwareHealthState.UNUSED

    service.start()
    assert service.health_state_actual == SoftwareHealthState.GOOD
    service.pause()
    assert service.operating_state == ServiceOperatingState.PAUSED
    assert service.health_state_actual == SoftwareHealthState.GOOD

    service.resume()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.GOOD


def test_restart(service):
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_actual == SoftwareHealthState.UNUSED
    service.restart()
    # Service is STOPPED. Restart will only work if the service was PAUSED or RUNNING
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_actual == SoftwareHealthState.UNUSED

    service.start()
    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.GOOD
    service.restart()
    # Service is RUNNING. Restart should work
    assert service.operating_state == ServiceOperatingState.RESTARTING
    assert service.health_state_actual == SoftwareHealthState.GOOD

    timestep = 0
    while service.operating_state == ServiceOperatingState.RESTARTING:
        service.apply_timestep(timestep)
        assert service.health_state_actual == SoftwareHealthState.GOOD
        timestep += 1

    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.GOOD


def test_restart_compromised(service):
    service.start()
    assert service.health_state_actual == SoftwareHealthState.GOOD

    # compromise the service
    service.set_health_state(SoftwareHealthState.COMPROMISED)

    service.restart()
    assert service.operating_state == ServiceOperatingState.RESTARTING
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    """
    Service should be compromised even after reset.

    Only way to remove compromised status is via FIXING.
    """

    timestep = 0
    while service.operating_state == ServiceOperatingState.RESTARTING:
        service.apply_timestep(timestep)
        assert service.health_state_actual == SoftwareHealthState.COMPROMISED
        timestep += 1

    assert service.operating_state == ServiceOperatingState.RUNNING
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED


def test_compromised_service_remains_compromised(service):
    """
    Tests that a compromised service stays compromised.

    The only way that the service can be uncompromised is by running patch.
    """
    service.start()
    assert service.health_state_actual == SoftwareHealthState.GOOD

    service.set_health_state(SoftwareHealthState.COMPROMISED)

    service.stop()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    service.start()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    service.disable()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    service.enable()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    service.pause()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED

    service.resume()
    assert service.health_state_actual == SoftwareHealthState.COMPROMISED


def test_service_fixing(service):
    service.start()
    assert service.health_state_actual == SoftwareHealthState.GOOD

    service.set_health_state(SoftwareHealthState.COMPROMISED)

    service.fix()
    assert service.health_state_actual == SoftwareHealthState.FIXING

    for i in range(service.fixing_duration + 1):
        service.apply_timestep(i)

    assert service.health_state_actual == SoftwareHealthState.GOOD


def test_enable_disable(service):
    service.disable()
    assert service.operating_state == ServiceOperatingState.DISABLED
    assert service.health_state_actual == SoftwareHealthState.UNUSED

    service.enable()
    assert service.operating_state == ServiceOperatingState.STOPPED
    assert service.health_state_actual == SoftwareHealthState.UNUSED


def test_overwhelm_service(service):
    service.max_sessions = 2
    service.start()

    uuid = str(uuid4())
    assert service.add_connection(connection_id=uuid)  # should be true
    assert service.health_state_actual == SoftwareHealthState.GOOD

    assert not service.add_connection(connection_id=uuid)  # fails because connection already exists
    assert service.health_state_actual == SoftwareHealthState.GOOD

    assert service.add_connection(connection_id=str(uuid4()))  # succeed
    assert service.health_state_actual == SoftwareHealthState.GOOD

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
