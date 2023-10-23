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
