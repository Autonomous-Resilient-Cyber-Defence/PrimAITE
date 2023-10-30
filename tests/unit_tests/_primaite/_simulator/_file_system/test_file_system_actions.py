from typing import Tuple

import pytest

from primaite.simulator.file_system.file_system import File, FileSystem, FileSystemItemHealthStatus, Folder


@pytest.fixture(scope="function")
def populated_file_system(file_system) -> Tuple[FileSystem, Folder, File]:
    """Test that an agent can request a file scan."""
    folder = file_system.create_folder(folder_name="test_folder")
    file = file_system.create_file(folder_name="test_folder", file_name="test_file.txt")

    return file_system, folder, file


def test_file_scan_request(populated_file_system):
    """Test that an agent can request a file scan."""
    fs, folder, file = populated_file_system

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    fs.apply_request(request=["file", file.uuid, "scan"])

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_scan_request(populated_file_system):
    """Test that an agent can request a folder scan."""
    fs, folder, file = populated_file_system
    fs.create_file(file_name="test_file2.txt", folder_name="test_folder")

    file1: File = folder.get_file_by_id(file_uuid=list(folder.files)[1])
    file2: File = folder.get_file_by_id(file_uuid=list(folder.files)[0])

    folder.corrupt()
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    fs.apply_request(request=["folder", folder.uuid, "scan"])

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


def test_file_checkhash_request(populated_file_system):
    """Test that an agent can request a file hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.health_status == FileSystemItemHealthStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_checkhash_request(populated_file_system):
    """Test that an agent can request a folder hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["folder", folder.uuid, "checkhash"])

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["folder", folder.uuid, "checkhash"])
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_repair_request(populated_file_system):
    """Test that an agent can request a file repair."""
    fs, folder, file = populated_file_system

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["file", file.uuid, "repair"])
    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_folder_repair_request(populated_file_system):
    """Test that an agent can request a folder repair."""
    fs, folder, file = populated_file_system

    folder.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["folder", folder.uuid, "repair"])
    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert folder.health_status == FileSystemItemHealthStatus.GOOD


def test_file_restore_request(populated_file_system):
    pass


def test_folder_restore_request(populated_file_system):
    pass


def test_file_corrupt_request(populated_file_system):
    """Test that an agent can request a file corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["file", file.uuid, "corrupt"])
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_corrupt_request(populated_file_system):
    """Test that an agent can request a folder corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["folder", folder.uuid, "corrupt"])
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_delete_request(populated_file_system):
    """Test that an agent can request a file deletion."""
    fs, folder, file = populated_file_system
    assert folder.get_file_by_id(file_uuid=file.uuid) is not None

    fs.apply_request(request=["folder", folder.uuid, "delete", file.uuid])
    assert folder.get_file_by_id(file_uuid=file.uuid) is None


def test_folder_delete_request(populated_file_system):
    """Test that an agent can request a folder deletion."""
    fs, folder, file = populated_file_system
    assert folder.get_file_by_id(file_uuid=file.uuid) is not None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None

    fs.apply_request(request=["delete", folder.uuid])
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is None
    assert folder.get_file_by_id(file_uuid=file.uuid) is None
