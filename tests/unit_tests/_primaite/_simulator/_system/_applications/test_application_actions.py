# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState


def test_application_state_validator(application):
    """Test the application state validator."""
    validator = Application._StateValidator(application=application, state=ApplicationOperatingState.CLOSED)
    assert validator(request=[], context={})  # application is closed
    application.run()
    assert validator(request=[], context={}) is False  # application is running - expecting closed

    validator = Application._StateValidator(application=application, state=ApplicationOperatingState.RUNNING)
    assert validator(request=[], context={})  # application is running
    application.close()
    assert validator(request=[], context={}) is False  # application is closed - expecting running
