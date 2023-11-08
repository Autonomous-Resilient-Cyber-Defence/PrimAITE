from typing import Tuple

import pytest

from src.primaite.simulator.file_system.file import File
from src.primaite.simulator.file_system.file_system import FileSystem
from src.primaite.simulator.file_system.folder import Folder


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

    fs.show(full=True)


def test_folder_delete_request(populated_file_system):
    """Test that an agent can request a folder deletion."""
    fs, folder, file = populated_file_system
    assert folder.get_file_by_id(file_uuid=file.uuid) is not None
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is not None

    fs.apply_request(request=["delete", "folder", folder.uuid])
    assert fs.get_folder_by_id(folder_uuid=folder.uuid) is None
    assert fs.get_file_by_id(folder_uuid=folder.uuid, file_uuid=file.uuid) is None

    fs.show(full=True)
