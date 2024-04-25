import pytest

from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.file_system.file_type import FileType


def test_create_file_no_extension(file_system):
    """Tests that creating a file without an extension sets the file type to FileType.UNKNOWN."""
    file = file_system.create_file(file_name="test_file")
    assert len(file_system.folders) is 1
    assert file_system.get_folder("root").get_file("test_file") == file
    assert file_system.get_folder("root").get_file("test_file").file_type == FileType.UNKNOWN
    assert file_system.get_folder("root").get_file("test_file").size == 0


def test_file_scan(file_system):
    """Test the ability to update visible status."""
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    file.corrupt()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    file.scan()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_reveal_to_red_scan(file_system):
    """Test the ability to reveal files to red."""
    file = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert file.revealed_to_red is False

    file.reveal_to_red()

    assert file.revealed_to_red is True


@pytest.mark.skip(reason="NODE_FILE_CHECKHASH not implemented")
def test_simulated_file_check_hash(file_system):
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    file.check_hash()
    assert file.health_status == FileSystemItemHealthStatus.GOOD
    # change simulated file size
    file.sim_size = 0
    file.check_hash()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


@pytest.mark.skip(reason="NODE_FILE_CHECKHASH not implemented")
def test_real_file_check_hash(file_system):
    file: File = file_system.create_file(file_name="test_file.txt", real=True)

    file.check_hash()
    assert file.health_status == FileSystemItemHealthStatus.GOOD
    # change file content
    with open(file.sim_path, "a") as f:
        f.write("get hacked scrub lol xD\n")

    file.check_hash()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_corrupt_repair_restore(file_system):
    """Test the ability to corrupt and repair files."""
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    file.repair()
    assert file.health_status == FileSystemItemHealthStatus.GOOD

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    file.restore()
    assert file.health_status == FileSystemItemHealthStatus.GOOD
