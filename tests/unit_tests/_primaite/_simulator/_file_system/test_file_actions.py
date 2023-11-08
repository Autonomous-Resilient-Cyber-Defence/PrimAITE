from typing import Tuple

import pytest

from src.primaite.simulator.file_system.file import File
from src.primaite.simulator.file_system.file_system import FileSystem
from src.primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from src.primaite.simulator.file_system.folder import Folder


@pytest.fixture(scope="function")
def populated_file_system(file_system) -> Tuple[FileSystem, Folder, File]:
    """Create a file system with a folder and file."""
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


def test_file_checkhash_request(populated_file_system):
    """Test that an agent can request a file hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.health_status == FileSystemItemHealthStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_repair_request(populated_file_system):
    """Test that an agent can request a file repair."""
    fs, folder, file = populated_file_system

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["file", file.uuid, "repair"])
    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_file_restore_request(populated_file_system):
    """Test that an agent can request that a file can be restored."""
    fs, folder, file = populated_file_system
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is not None

    fs.apply_request(request=["delete", "file", folder.uuid, file.uuid])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is True

    fs.apply_request(request=["restore", "file", folder.uuid, file.uuid])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None
    assert fs.get_file(folder_name=folder.name, file_name=file.name).deleted is False

    fs.apply_request(request=["file", file.uuid, "corrupt"])
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["restore", "file", folder.uuid, file.uuid])
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.GOOD


def test_file_corrupt_request(populated_file_system):
    """Test that an agent can request a file corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["file", file.uuid, "corrupt"])
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_deleted_file_cannot_be_interacted_with(populated_file_system):
    """Test that actions cannot affect deleted files."""
    fs, folder, file = populated_file_system
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None

    fs.apply_request(request=["file", file.uuid, "corrupt"])
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT
    assert (
        fs.get_file(folder_name=folder.name, file_name=file.name).visible_health_status
        == FileSystemItemHealthStatus.GOOD
    )

    fs.apply_request(request=["delete", "file", folder.uuid, file.uuid])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None

    fs.apply_request(request=["file", file.uuid, "repair"])
    fs.apply_request(request=["file", file.uuid, "scan"])

    file = folder.deleted_files.get(file.uuid)

    assert file.health_status is not FileSystemItemHealthStatus.GOOD
    assert file.visible_health_status is not FileSystemItemHealthStatus.CORRUPT
