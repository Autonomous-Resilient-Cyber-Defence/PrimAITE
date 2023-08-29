from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.database import DatabaseService
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareCriticality, SoftwareHealthState


def test_installing_database():
    db = DatabaseService(
        name="SQL-database",
        health_state_actual=SoftwareHealthState.GOOD,
        health_state_visible=SoftwareHealthState.GOOD,
        criticality=SoftwareCriticality.MEDIUM,
        ports=[
            Port.SQL_SERVER,
        ],
        operating_state=ServiceOperatingState.RUNNING,
    )

    node = Node(hostname="db-server")

    node.install_service(db)
