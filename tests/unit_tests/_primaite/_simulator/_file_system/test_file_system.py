import pytest

from primaite.simulator.file_system.file_system import File, FileSystem, Folder
from primaite.simulator.file_system.file_type import FileType
from primaite.simulator.network.hardware.base import Node


@pytest.fixture(scope="function")
def file_system() -> FileSystem:
    return Node(hostname="fs_node").file_system


def test_create_folder_and_file(file_system):
    """Test creating a folder and a file."""
    assert len(file_system.folders) == 1
    test_folder = file_system.create_folder(folder_name="test_folder")

    assert len(file_system.folders) is 2
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert len(file_system.get_folder("test_folder").files) == 1

    assert file_system.get_folder("test_folder").get_file("test_file.txt")


def test_create_file_no_folder(file_system):
    """Tests that creating a file without a folder creates a folder and sets that as the file's parent."""
    file = file_system.create_file(file_name="test_file.txt", size=10)
    assert len(file_system.folders) is 1
    assert file_system.get_folder("root").get_file("test_file.txt") == file
    assert file_system.get_folder("root").get_file("test_file.txt").file_type == FileType.TXT
    assert file_system.get_folder("root").get_file("test_file.txt").size == 10


def test_create_file_no_extension(file_system):
    """Tests that creating a file without an extension sets the file type to FileType.UNKNOWN."""
    file = file_system.create_file(file_name="test_file")
    assert len(file_system.folders) is 1
    assert file_system.get_folder("root").get_file("test_file") == file
    assert file_system.get_folder("root").get_file("test_file").file_type == FileType.UNKNOWN
    assert file_system.get_folder("root").get_file("test_file").size == 0


def test_delete_file(file_system):
    """Tests that a file can be deleted."""
    file_system.create_file(file_name="test_file.txt")
    assert len(file_system.folders) == 1
    assert len(file_system.get_folder("root").files) == 1

    file_system.delete_file(folder_name="root", file_name="test_file.txt")
    assert len(file_system.folders) == 1
    assert len(file_system.get_folder("root").files) == 0


def test_delete_non_existent_file(file_system):
    """Tests deleting a non existent file."""
    file_system.create_file(file_name="test_file.txt")
    # folder should be created
    assert len(file_system.folders) == 1
    # should only have 1 file in the file system
    assert len(file_system.get_folder("root").files) == 1

    # deleting should not change how many files are in folder
    file_system.delete_file(folder_name="root", file_name="does_not_exist!")

    # should still only be one folder
    assert len(file_system.folders) == 1
    # The folder should still have 1 file
    assert len(file_system.get_folder("root").files) == 1


def test_delete_folder(file_system):
    file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) == 2

    file_system.delete_folder(folder_name="test_folder")
    assert len(file_system.folders) == 1


def test_deleting_a_non_existent_folder(file_system):
    file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) == 2

    file_system.delete_folder(folder_name="does not exist!")
    assert len(file_system.folders) == 2


def test_deleting_root_folder_fails(file_system):
    assert len(file_system.folders) == 1

    file_system.delete_folder(folder_name="root")
    assert len(file_system.folders) == 1


def test_move_file(file_system):
    """Tests the file move function."""
    file_system.create_folder(folder_name="src_folder")
    file_system.create_folder(folder_name="dst_folder")

    file = file_system.create_file(file_name="test_file.txt", size=10, folder_name="src_folder")
    original_uuid = file.uuid

    assert len(file_system.get_folder("src_folder").files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 0

    file_system.move_file(src_folder_name="src_folder", src_file_name="test_file.txt", dst_folder_name="dst_folder")

    assert len(file_system.get_folder("src_folder").files) == 0
    assert len(file_system.get_folder("dst_folder").files) == 1
    assert file_system.get_file("dst_folder", "test_file.txt").uuid == original_uuid


def test_copy_file(file_system):
    """Tests the file copy function."""
    file_system.create_folder(folder_name="src_folder")
    file_system.create_folder(folder_name="dst_folder")

    file = file_system.create_file(file_name="test_file.txt", size=10, folder_name="src_folder")
    original_uuid = file.uuid

    assert len(file_system.get_folder("src_folder").files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 0

    file_system.copy_file(src_folder_name="src_folder", src_file_name="test_file.txt", dst_folder_name="dst_folder")

    assert len(file_system.get_folder("src_folder").files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 1
    assert file_system.get_file("dst_folder", "test_file.txt").uuid != original_uuid


@pytest.mark.skip(reason="Skipping until we tackle serialisation")
def test_serialisation(file_system):
    """Test to check that the object serialisation works correctly."""
    file_system.create_file(file_name="test_file.txt")

    serialised_file_sys = file_system.model_dump_json()
    deserialised_file_sys = FileSystem.model_validate_json(serialised_file_sys)

    assert file_system.model_dump_json() == deserialised_file_sys.model_dump_json()
