# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.system.applications.application import Application


def test_adding_to_app_registry():
    class temp_application(Application, discriminator="temp-app"):
        pass

    assert Application._registry["temp-app"] is temp_application

    with pytest.raises(ValueError):

        class another_application(Application, discriminator="temp-app"):
            pass

    # This is kinda evil...
    # Because pytest doesn't reimport classes from modules, registering this temporary test application will change the
    # state of the Application registry for all subsequently run tests. So, we have to delete and unregister the class.
    del temp_application
    Application._registry.pop("temp-app")
