# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.file_system.folder import Folder


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

    fs.apply_request(request=["delete", "file", folder.name, file.name])
    assert fs.get_file(folder_name=folder.name, file_name=file.name) is None

    fs.show(full=True)


def test_folder_delete_request(populated_file_system):
    """Test that an agent can request a folder deletion."""
    fs, folder, file = populated_file_system
    assert folder.get_file_by_id(file_uuid=file.uuid) is not None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None

    fs.apply_request(request=["delete", "folder", folder.name])
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is None

    fs.show(full=True)


def test_folder_exists_request_validator(populated_file_system):
    """Tests that the _FolderExistsValidator works as intended."""
    fs, folder, file = populated_file_system
    validator = FileSystem._FolderExistsValidator(file_system=fs)

    assert validator(request=["test_folder"], context={})  # test_folder exists
    assert validator(request=["fake_folder"], context={}) is False  # fake_folder does not exist

    assert validator.fail_message == "Cannot perform request on folder because it does not exist."


def test_file_exists_request_validator(populated_file_system):
    """Tests that the _FolderExistsValidator works as intended."""
    fs, folder, file = populated_file_system
    validator = FileSystem._FileExistsValidator(file_system=fs)

    assert validator(request=["test_folder", "test_file.txt"], context={})  # test_file.txt exists
    assert validator(request=["test_folder", "fake_file.txt"], context={}) is False  # fake_file.txt does not exist

    assert validator.fail_message == "Cannot perform request on a file that does not exist."


def test_folder_not_deleted_request_validator(populated_file_system):
    """Tests that the _FolderExistsValidator works as intended."""
    fs, folder, file = populated_file_system
    validator = FileSystem._FolderNotDeletedValidator(file_system=fs)

    assert validator(request=["test_folder"], context={})  # test_folder is not deleted

    fs.delete_folder(folder_name="test_folder")

    assert validator(request=["test_folder"], context={}) is False  # test_folder is deleted

    assert validator.fail_message == "Cannot perform request on folder because it is deleted."
