from typing import Tuple

import pytest

from primaite.simulator.file_system.file_system import File, FileSystem, Folder
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus


@pytest.fixture(scope="function")
def populated_file_system(file_system) -> Tuple[FileSystem, Folder, File]:
    """Create a file system with a folder and file."""
    folder = file_system.create_folder(folder_name="test_folder")
    file = file_system.create_file(folder_name="test_folder", file_name="test_file.txt")

    return file_system, folder, file


def test_file_delete_request(populated_file_system):
    """Test that an agent can request a file deletion."""
    fs, folder, file = populated_file_system
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None

    fs.apply_request(request=["delete", "file", folder.uuid, file.uuid])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None


def test_folder_delete_request(populated_file_system):
    """Test that an agent can request a folder deletion."""
    fs, folder, file = populated_file_system
    assert folder.get_file_by_id(file_uuid=file.uuid) is not None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None

    fs.apply_request(request=["delete", "folder", folder.uuid])
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is None


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


def test_folder_restore_request(populated_file_system):
    """Test that an agent can request that a folder can be restored."""
    fs, folder, file = populated_file_system
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is not None

    # delete folder
    fs.apply_request(request=["delete", "folder", folder.uuid])
    assert fs.get_folder(folder_name=folder.name) is None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid, include_deleted=True).deleted is True

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is True

    # restore folder
    fs.apply_request(request=["restore", "folder", folder.uuid])
    fs.apply_timestep(timestep=0)
    assert fs.get_folder(folder_name=folder.name) is not None
    assert (
        fs.get_folder_by_id(folder_uuid=folder.uuid, include_deleted=True).health_status
        == FileSystemItemHealthStatus.RESTORING
    )
    assert fs.get_folder_by_id(folder_uuid=folder.uuid, include_deleted=True).deleted is False

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is True

    fs.apply_timestep(timestep=1)
    fs.apply_timestep(timestep=2)

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None
    assert (
        fs.get_file(folder_name=folder.name, file_name=file.name).health_status
        is not FileSystemItemHealthStatus.RESTORING
    )
    assert fs.get_file(folder_name=folder.name, file_name=file.name).deleted is False

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is False

    # corrupt folder
    fs.apply_request(request=["folder", folder.uuid, "corrupt"])
    assert fs.get_folder(folder_name=folder.name).health_status == FileSystemItemHealthStatus.CORRUPT
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT

    # restore folder
    fs.apply_request(request=["restore", "folder", folder.uuid])
    fs.apply_timestep(timestep=0)
    assert fs.get_folder(folder_name=folder.name).health_status == FileSystemItemHealthStatus.RESTORING
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_timestep(timestep=1)
    fs.apply_timestep(timestep=2)

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None
    assert (
        fs.get_file(folder_name=folder.name, file_name=file.name).health_status
        is not FileSystemItemHealthStatus.RESTORING
    )
    assert fs.get_file(folder_name=folder.name, file_name=file.name).deleted is False

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is False
