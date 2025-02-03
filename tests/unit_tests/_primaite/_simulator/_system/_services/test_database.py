# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.services.database.database_service import DatabaseService


@pytest.fixture(scope="function")
def database_server() -> Node:
    node = Computer(hostname="db_node", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)
    node.power_on()
    node.software_manager.install(DatabaseService)
    node.software_manager.software.get("database-service").start()
    return node


def test_creation(database_server):
    database_server.software_manager.show()
