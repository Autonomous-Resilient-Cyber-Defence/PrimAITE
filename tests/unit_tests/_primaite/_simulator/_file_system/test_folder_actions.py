# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import warnings
from typing import Tuple

import pytest

from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.file_system.folder import Folder


@pytest.fixture(scope="function")
def populated_file_system(file_system) -> Tuple[FileSystem, Folder, File]:
    """Create a file system with a folder and file."""
    folder = file_system.create_folder(folder_name="test_folder")
    file = file_system.create_file(folder_name="test_folder", file_name="test_file.txt")

    return file_system, folder, file


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

    fs.apply_request(request=["folder", folder.name, "scan"])

    folder.apply_timestep(timestep=0)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.apply_timestep(timestep=1)
    folder.apply_timestep(timestep=2)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file1.visible_health_status == FileSystemItemHealthStatus.CORRUPT
    assert file2.visible_health_status == FileSystemItemHealthStatus.CORRUPT


@pytest.mark.skip(reason="NODE_FOLDER_CHECKHASH not implemented")
def test_folder_checkhash_request(populated_file_system):
    """Test that an agent can request a folder hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["folder", folder.name, "checkhash"])

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["folder", folder.name, "checkhash"])
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_warning_triggered(populated_file_system):
    fs, folder, _ = populated_file_system
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fs.apply_request(request=["folder", folder.name, "checkhash"])
        # Check warning issued
        assert len(w) == 1
        assert "not implemented" in str(w[-1].message)


def test_folder_repair_request(populated_file_system):
    """Test that an agent can request a folder repair."""
    fs, folder, file = populated_file_system

    folder.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["folder", folder.name, "repair"])
    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert folder.health_status == FileSystemItemHealthStatus.GOOD


def test_folder_restore_request(populated_file_system):
    """Test that an agent can request that a folder can be restored."""
    fs, folder, file = populated_file_system
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is not None

    # delete folder
    fs.apply_request(request=["delete", "folder", folder.name])
    assert fs.get_folder(folder_name=folder.name) is None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid, include_deleted=True).deleted is True

    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid, include_deleted=True).deleted is True

    # restore folder
    fs.apply_request(request=["restore", "folder", folder.name])
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
    fs.apply_request(request=["folder", folder.name, "corrupt"])
    assert fs.get_folder(folder_name=folder.name).health_status == FileSystemItemHealthStatus.CORRUPT
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT

    # restore folder
    fs.apply_request(request=["restore", "folder", folder.name])
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


def test_folder_corrupt_request(populated_file_system):
    """Test that an agent can request a folder corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["folder", folder.name, "corrupt"])
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT


def test_deleted_folder_and_its_files_cannot_be_interacted_with(populated_file_system):
    """Test that actions cannot affect deleted folder and its child files."""
    fs, folder, file = populated_file_system
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is not None

    fs.apply_request(request=["folder", folder.name, "file", file.name, "corrupt"])
    assert fs.get_file(folder_name=folder.name, file_name=file.name).health_status == FileSystemItemHealthStatus.CORRUPT

    fs.apply_request(request=["delete", "folder", folder.name])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None

    fs.apply_request(request=["folder", folder.name, "file", file.name, "repair"])

    deleted_folder = fs.deleted_folders.get(folder.uuid)
    deleted_file = deleted_folder.deleted_files.get(file.uuid)

    assert deleted_file.health_status is not FileSystemItemHealthStatus.GOOD


def test_file_exists_request_validator(populated_file_system):
    """Tests that the _FolderExistsValidator works as intended."""
    fs, folder, file = populated_file_system
    validator = Folder._FileExistsValidator(folder=folder)

    assert validator(request=["test_file.txt"], context={})  # test_file.txt exists
    assert validator(request=["fake_file.txt"], context={}) is False  # fake_file.txt does not exist

    assert validator.fail_message == "Cannot perform request on a file that does not exist."


def test_file_not_deleted_request_validator(populated_file_system):
    """Tests that the _FolderExistsValidator works as intended."""
    fs, folder, file = populated_file_system
    validator = Folder._FileNotDeletedValidator(folder=folder)

    assert validator(request=["test_file.txt"], context={})  # test_file.txt is not deleted

    fs.delete_file(folder_name="test_folder", file_name="test_file.txt")

    assert validator(request=["fake_file.txt"], context={}) is False  # test_file.txt is deleted

    assert validator.fail_message == "Cannot perform request on a file that is deleted."
