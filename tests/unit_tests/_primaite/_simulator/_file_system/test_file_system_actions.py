from typing import Tuple

import pytest

from primaite.simulator.file_system.file_system import File, FileSystem, FileSystemItemStatus, Folder


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
    assert file.status == FileSystemItemStatus.CORRUPTED
    assert file.visible_status == FileSystemItemStatus.GOOD

    fs.apply_request(request=["file", file.uuid, "scan"])

    assert file.status == FileSystemItemStatus.CORRUPTED
    assert file.visible_status == FileSystemItemStatus.CORRUPTED


def test_folder_scan_request(populated_file_system):
    """Test that an agent can request a folder scan."""
    fs, folder, file = populated_file_system

    folder.corrupt()
    assert folder.status == FileSystemItemStatus.CORRUPTED
    assert file.status == FileSystemItemStatus.CORRUPTED
    assert folder.visible_status == FileSystemItemStatus.GOOD
    assert file.visible_status == FileSystemItemStatus.GOOD

    fs.apply_request(request=["folder", folder.uuid, "scan"])

    assert folder.status == FileSystemItemStatus.CORRUPTED
    assert file.status == FileSystemItemStatus.CORRUPTED
    assert folder.visible_status == FileSystemItemStatus.CORRUPTED
    assert file.visible_status == FileSystemItemStatus.CORRUPTED


def test_file_checkhash_request(populated_file_system):
    """Test that an agent can request a file hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.status == FileSystemItemStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["file", file.uuid, "checkhash"])

    assert file.status == FileSystemItemStatus.CORRUPTED


def test_folder_checkhash_request(populated_file_system):
    """Test that an agent can request a folder hash check."""
    fs, folder, file = populated_file_system

    fs.apply_request(request=["folder", folder.uuid, "checkhash"])

    assert folder.status == FileSystemItemStatus.GOOD
    file.sim_size = 0

    fs.apply_request(request=["folder", folder.uuid, "checkhash"])
    assert folder.status == FileSystemItemStatus.CORRUPTED


def test_file_repair_request(populated_file_system):
    """Test that an agent can request a file repair."""
    fs, folder, file = populated_file_system

    file.corrupt()
    assert file.status == FileSystemItemStatus.CORRUPTED

    fs.apply_request(request=["file", file.uuid, "repair"])
    assert file.status == FileSystemItemStatus.GOOD


def test_folder_repair_request(populated_file_system):
    """Test that an agent can request a folder repair."""
    fs, folder, file = populated_file_system

    folder.corrupt()
    assert file.status == FileSystemItemStatus.CORRUPTED
    assert folder.status == FileSystemItemStatus.CORRUPTED

    fs.apply_request(request=["folder", folder.uuid, "repair"])
    assert file.status == FileSystemItemStatus.GOOD
    assert folder.status == FileSystemItemStatus.GOOD


def test_file_restore_request(populated_file_system):
    pass


def test_folder_restore_request(populated_file_system):
    pass


def test_file_corrupt_request(populated_file_system):
    """Test that an agent can request a file corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["file", file.uuid, "corrupt"])
    assert file.status == FileSystemItemStatus.CORRUPTED


def test_folder_corrupt_request(populated_file_system):
    """Test that an agent can request a folder corruption."""
    fs, folder, file = populated_file_system
    fs.apply_request(request=["folder", folder.uuid, "corrupt"])
    assert file.status == FileSystemItemStatus.CORRUPTED
    assert folder.status == FileSystemItemStatus.CORRUPTED


def test_file_delete_request(populated_file_system):
    pass


def test_folder_delete_request(populated_file_system):
    pass
