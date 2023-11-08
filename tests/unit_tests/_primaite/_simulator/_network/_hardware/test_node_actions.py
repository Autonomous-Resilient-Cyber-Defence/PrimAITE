import pytest

from src.primaite.simulator.file_system.file import File
from src.primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from src.primaite.simulator.file_system.folder import Folder
from src.primaite.simulator.network.hardware.base import Node, NodeOperatingState
from src.primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture
def node() -> Node:
    return Node(hostname="test")


def test_node_startup(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    assert node.operating_state == NodeOperatingState.BOOTING

    idx = 0
    while node.operating_state == NodeOperatingState.BOOTING:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.ON


def test_node_shutdown(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    idx = 0
    while node.operating_state == NodeOperatingState.BOOTING:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.ON

    node.apply_request(["shutdown"])

    idx = 0
    while node.operating_state == NodeOperatingState.SHUTTING_DOWN:
        node.apply_timestep(timestep=idx)
        idx += 1

    assert node.operating_state == NodeOperatingState.OFF


def test_node_os_scan(node, service, application):
    """Test OS Scanning."""
    node.operating_state = NodeOperatingState.ON

    # add process to node
    # TODO implement processes

    # add services to node
    service.health_state_actual = SoftwareHealthState.COMPROMISED
    node.install_service(service=service)
    assert service.health_state_visible == SoftwareHealthState.UNUSED

    # add application to node
    application.health_state_actual = SoftwareHealthState.COMPROMISED
    node.install_application(application=application)
    assert application.health_state_visible == SoftwareHealthState.UNUSED

    # add folder and file to node
    folder: Folder = node.file_system.create_folder(folder_name="test_folder")
    folder.corrupt()
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD

    file: File = node.file_system.create_file(folder_name="test_folder", file_name="file.txt")
    file2: File = node.file_system.create_file(folder_name="test_folder", file_name="file2.txt")
    file.corrupt()
    file2.corrupt()
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    # run os scan
    node.apply_request(["os", "scan"])

    # apply time steps
    for i in range(10):
        node.apply_timestep(timestep=i)

    # should update the state of all items
    # TODO assert process.health_state_visible == SoftwareHealthState.COMPROMISED
    assert service.health_state_visible == SoftwareHealthState.COMPROMISED
    assert application.health_state_visible == SoftwareHealthState.COMPROMISED
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file2.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_node_red_scan(node, service, application):
    """Test revealing to red"""
    node.operating_state = NodeOperatingState.ON

    # add process to node
    # TODO implement processes

    # add services to node
    node.install_service(service=service)
    assert service.revealed_to_red is False

    # add application to node
    application.health_state_actual = SoftwareHealthState.COMPROMISED
    node.install_application(application=application)
    assert application.revealed_to_red is False

    # add folder and file to node
    folder: Folder = node.file_system.create_folder(folder_name="test_folder")
    assert folder.revealed_to_red is False

    file: File = node.file_system.create_file(folder_name="test_folder", file_name="file.txt")
    file2: File = node.file_system.create_file(folder_name="test_folder", file_name="file2.txt")
    assert file.revealed_to_red is False
    assert file2.revealed_to_red is False

    # run os scan
    node.apply_request(["scan"])

    # apply time steps
    for i in range(10):
        node.apply_timestep(timestep=i)

    # should update the state of all items
    # TODO assert process.revealed_to_red is True
    assert service.revealed_to_red is True
    assert application.revealed_to_red is True
    assert folder.revealed_to_red is True
    assert file.revealed_to_red is True
    assert file2.revealed_to_red is True


def test_reset_node(node):
    """Test that a node can be reset."""
    node.operating_state = NodeOperatingState.ON

    node.apply_request(["reset"])
    assert node.operating_state == NodeOperatingState.SHUTTING_DOWN

    """
    3 steps to shut down
    2 steps to set up the turning of it back on
    3 steps to turn back on

    3 + 2 + 3 = 8
    kwik mafs
    """

    for i in range(8):
        node.apply_timestep(timestep=i)

        if i == 3:
            assert node.operating_state == NodeOperatingState.BOOTING

    assert node.operating_state == NodeOperatingState.ON
