# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.file_system.folder import Folder
from primaite.simulator.network.hardware.base import Node, NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.software import SoftwareHealthState
from tests.conftest import DummyApplication, DummyService


@pytest.fixture
def node() -> Node:
    computer_cfg = {
        "type": "computer",
        "hostname": "test",
        "ip_address": "192.168.1.2",
        "subnet_mask": "255.255.255.0",
        "operating_state": "OFF",
    }
    computer = Computer.from_config(config=computer_cfg)

    return computer


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


def test_node_os_scan(node):
    """Test OS Scanning."""
    node.operating_state = NodeOperatingState.ON

    # add process to node
    # TODO implement processes

    # add services to node
    node.software_manager.install(DummyService)
    service = node.software_manager.software.get("dummy-service")
    service.set_health_state(SoftwareHealthState.COMPROMISED)
    assert service.health_state_visible == SoftwareHealthState.UNUSED

    # add application to node
    node.software_manager.install(DummyApplication)
    application = node.software_manager.software.get("dummy-application")
    application.set_health_state(SoftwareHealthState.COMPROMISED)
    assert application.health_state_visible == SoftwareHealthState.UNUSED

    # add folder and file to node
    folder: Folder = node.file_system.create_folder(folder_name="test_folder")
    folder.corrupt()
    assert folder.visible_health_status == FileSystemItemHealthStatus.NONE

    file: File = node.file_system.create_file(folder_name="test_folder", file_name="file.txt")
    file2: File = node.file_system.create_file(folder_name="test_folder", file_name="file2.txt")
    file.corrupt()
    file2.corrupt()
    assert file.visible_health_status == FileSystemItemHealthStatus.NONE

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


def test_node_red_scan(node):
    """Test revealing to red"""
    node.operating_state = NodeOperatingState.ON

    # add process to node
    # TODO implement processes

    # add services to node
    node.software_manager.install(DummyService)
    service = node.software_manager.software.get("dummy-service")
    assert service.revealed_to_red is False

    # add application to node
    node.software_manager.install(DummyApplication)
    application = node.software_manager.software.get("dummy-application")
    application.set_health_state(SoftwareHealthState.COMPROMISED)
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


def test_node_is_on_validator(node):
    """Test that the node is on validator."""
    node.power_on()

    for i in range(node.config.start_up_duration + 1):
        node.apply_timestep(i)

    validator = Node._NodeIsOnValidator(node=node)

    assert validator(request=[], context={})

    node.power_off()
    for i in range(node.config.shut_down_duration + 1):
        node.apply_timestep(i)

    assert validator(request=[], context={}) is False


def test_node_is_off_validator(node):
    """Test that the node is on validator."""
    node.power_on()

    for i in range(node.config.start_up_duration + 1):
        node.apply_timestep(i)

    validator = Node._NodeIsOffValidator(node=node)

    assert validator(request=[], context={}) is False

    node.power_off()
    for i in range(node.config.shut_down_duration + 1):
        node.apply_timestep(i)

    assert validator(request=[], context={})
