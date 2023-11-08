import pytest

from src.primaite.simulator.network.hardware.base import Node
from src.primaite.simulator.system.services.database.database_service import DatabaseService


@pytest.fixture(scope="function")
def database_server() -> Node:
    node = Node(hostname="db_node")
    node.software_manager.install(DatabaseService)
    node.software_manager.software["DatabaseService"].start()
    return node


def test_creation(database_server):
    database_server.software_manager.show()
