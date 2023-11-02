import pytest

from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.file_system.folder import Folder


@pytest.mark.skip(reason="Implementation for quarantine not needed yet")
def test_folder_quarantine_state(file_system):
    """Tests the changing of folder quarantine status."""
    folder = file_system.get_folder("root")

    assert folder.quarantine_status() is False

    folder.quarantine()
    assert folder.quarantine_status() is True

    folder.unquarantine()
    assert folder.quarantine_status() is False


def test_folder_scan(file_system):
    """Test the ability to update visible status."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")
    file_system.create_file(file_name="test_file2.txt", folder_name="test_folder")

    file1: File = folder.get_file_by_id(file_uuid=list(folder.files)[1])
    file2: File = folder.get_file_by_id(file_uuid=list(folder.files)[0])

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.corrupt()

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.scan()

    folder.apply_timestep(timestep=0)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.apply_timestep(timestep=1)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file1.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file2.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_reveal_to_red_scan(file_system):
    """Test the ability to reveal files to red."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")
    file_system.create_file(file_name="test_file2.txt", folder_name="test_folder")

    file1: File = folder.get_file_by_id(file_uuid=list(folder.files)[1])
    file2: File = folder.get_file_by_id(file_uuid=list(folder.files)[0])

    assert folder.revealed_to_red is False
    assert file1.revealed_to_red is False
    assert file2.revealed_to_red is False

    folder.reveal_to_red()

    folder.apply_timestep(timestep=0)

    assert folder.revealed_to_red is False
    assert file1.revealed_to_red is False
    assert file2.revealed_to_red is False

    folder.apply_timestep(timestep=1)

    assert folder.revealed_to_red is True
    assert file1.revealed_to_red is True
    assert file2.revealed_to_red is True


def test_folder_corrupt_repair(file_system):
    """Test the ability to corrupt and repair folders."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    folder.corrupt()

    file = folder.get_file(file_name="test_file.txt")
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    folder.repair()

    file = folder.get_file(file_name="test_file.txt")
    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_simulated_folder_check_hash(file_system):
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert folder.check_hash() is True

    # change simulated file size
    file = folder.get_file(file_name="test_file.txt")
    file.sim_size = 0
    assert folder.check_hash() is False
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT


def test_real_folder_check_hash(file_system):
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder", real=True)

    assert folder.check_hash() is True

    # change simulated file size
    file = folder.get_file(file_name="test_file.txt")

    # change file content
    with open(file.sim_path, "a") as f:
        f.write("get hacked scrub lol xD\n")

    assert folder.check_hash() is False
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
