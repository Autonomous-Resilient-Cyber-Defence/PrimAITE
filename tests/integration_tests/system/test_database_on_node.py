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
        port=Port.SQL_SERVER,
        operating_state=ServiceOperatingState.RUNNING,
    )

    node = Node(hostname="db-server")

    node.install_service(db)

    assert db in node

    file_exists = False
    for folder in node.file_system.folders.values():
        for file in folder.files.values():
            if file.name == "db_primary_store":
                file_exists = True
                break
        if file_exists:
            break
    assert file_exists


def test_uninstalling_database():
    db = DatabaseService(
        name="SQL-database",
        health_state_actual=SoftwareHealthState.GOOD,
        health_state_visible=SoftwareHealthState.GOOD,
        criticality=SoftwareCriticality.MEDIUM,
        port=Port.SQL_SERVER,
        operating_state=ServiceOperatingState.RUNNING,
    )

    node = Node(hostname="db-server")

    node.install_service(db)

    node.uninstall_service(db)

    assert db not in node
    assert node.file_system.get_folder("database") is None
