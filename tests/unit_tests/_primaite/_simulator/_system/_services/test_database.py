from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.database import DatabaseService
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareCriticality, SoftwareHealthState


def test_creation():
    db = DatabaseService(
        name="SQL-database",
        health_state_actual=SoftwareHealthState.GOOD,
        health_state_visible=SoftwareHealthState.GOOD,
        criticality=SoftwareCriticality.MEDIUM,
        port=Port.SQL_SERVER,
        operating_state=ServiceOperatingState.RUNNING,
    )
