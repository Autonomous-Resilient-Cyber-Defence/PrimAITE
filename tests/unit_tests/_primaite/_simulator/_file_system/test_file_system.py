import pytest

from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.file_system.file_type import FileType


def test_create_folder_and_file(file_system):
    """Test creating a folder and a file."""
    assert len(file_system.folders) == 1
    file_system.create_folder(folder_name="test_folder")

    assert len(file_system.folders) is 2
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert len(file_system.get_folder("test_folder").files) == 1

    assert file_system.get_folder("test_folder").get_file("test_file.txt")

    file_system.show(full=True)


def test_create_file_no_folder(file_system):
    """Tests that creating a file without a folder creates a folder and sets that as the file's parent."""
    file = file_system.create_file(file_name="test_file.txt", size=10)
    assert len(file_system.folders) is 1
    assert file_system.get_folder("root").get_file("test_file.txt") == file
    assert file_system.get_folder("root").get_file("test_file.txt").file_type == FileType.TXT
    assert file_system.get_folder("root").get_file("test_file.txt").size == 10

    file_system.show(full=True)


def test_delete_file(file_system):
    """Tests that a file can be deleted."""
    file_system.create_file(file_name="test_file.txt")
    assert len(file_system.folders) == 1
    assert len(file_system.get_folder("root").files) == 1

    file_system.delete_file(folder_name="root", file_name="test_file.txt")
    assert len(file_system.folders) == 1
    assert len(file_system.get_folder("root").files) == 0
    assert len(file_system.get_folder("root").deleted_files) == 1

    file_system.show(full=True)


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

    file_system.show(full=True)


def test_delete_folder(file_system):
    file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) == 2

    file_system.delete_folder(folder_name="test_folder")
    assert len(file_system.folders) == 1

    assert len(file_system.deleted_folders) == 1

    file_system.show(full=True)


def test_create_duplicate_folder(file_system):
    """Test that creating a duplicate folder throws exception."""
    assert len(file_system.folders) == 1
    file_system.create_folder(folder_name="test_folder")

    assert len(file_system.folders) is 2
    with pytest.raises(Exception):
        file_system.create_folder(folder_name="test_folder")

    assert len(file_system.folders) is 2

    file_system.show(full=True)


def test_create_duplicate_file(file_system):
    """Test that creating a duplicate file throws exception."""
    assert len(file_system.folders) == 1
    file_system.create_folder(folder_name="test_folder")

    assert len(file_system.folders) is 2
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert len(file_system.get_folder("test_folder").files) == 1

    with pytest.raises(Exception):
        file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert len(file_system.get_folder("test_folder").files) == 1

    file_system.show(full=True)


def test_deleting_a_non_existent_folder(file_system):
    file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) == 2

    file_system.delete_folder(folder_name="does not exist!")
    assert len(file_system.folders) == 2

    file_system.show(full=True)


def test_deleting_root_folder_fails(file_system):
    assert len(file_system.folders) == 1

    file_system.delete_folder(folder_name="root")
    assert len(file_system.folders) == 1

    file_system.show(full=True)


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

    file_system.show(full=True)


def test_copy_file(file_system):
    """Tests the file copy function."""
    file_system.create_folder(folder_name="src_folder")
    file_system.create_folder(folder_name="dst_folder")

    file = file_system.create_file(file_name="test_file.txt", size=10, folder_name="src_folder", real=True)
    original_uuid = file.uuid

    assert len(file_system.get_folder("src_folder").files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 0

    file_system.copy_file(src_folder_name="src_folder", src_file_name="test_file.txt", dst_folder_name="dst_folder")

    assert len(file_system.get_folder("src_folder").files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 1
    assert file_system.get_file("dst_folder", "test_file.txt").uuid != original_uuid

    file_system.show(full=True)


def test_get_file(file_system):
    """Test that files can be retrieved."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file1: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")
    file2: File = file_system.create_file(file_name="test_file2.txt", folder_name="test_folder")

    folder.remove_file(file2)

    assert file_system.get_file_by_id(file_uuid=file1.uuid, folder_uuid=folder.uuid) is not None
    assert file_system.get_file_by_id(file_uuid=file2.uuid, folder_uuid=folder.uuid) is None
    assert file_system.get_file_by_id(file_uuid=file2.uuid, folder_uuid=folder.uuid, include_deleted=True) is not None
    assert file_system.get_file_by_id(file_uuid=file2.uuid, include_deleted=True) is not None

    file_system.delete_folder(folder_name="test_folder")
    assert file_system.get_file_by_id(file_uuid=file2.uuid, include_deleted=True) is not None

    file_system.show(full=True)


def test_reset_file_system(file_system):
    # file and folder that existed originally
    file_system.create_file(file_name="test_file.zip")
    file_system.create_folder(folder_name="test_folder")

    # create a new file
    file_system.create_file(file_name="new_file.txt")

    # create a new folder
    file_system.create_folder(folder_name="new_folder")

    # delete the file that existed originally
    file_system.delete_file(folder_name="root", file_name="test_file.zip")
    assert file_system.get_file(folder_name="root", file_name="test_file.zip") is None

    # delete the folder that existed originally
    file_system.delete_folder(folder_name="test_folder")
    assert file_system.get_folder(folder_name="test_folder") is None

    # reset
    file_system.reset_component_for_episode(episode=1)

    # deleted original file and folder should be back
    assert file_system.get_file(folder_name="root", file_name="test_file.zip")
    assert file_system.get_folder(folder_name="test_folder")

    # new file and folder should be removed
    assert file_system.get_file(folder_name="root", file_name="new_file.txt") is None
    assert file_system.get_folder(folder_name="new_folder") is None


@pytest.mark.skip(reason="Skipping until we tackle serialisation")
def test_serialisation(file_system):
    """Test to check that the object serialisation works correctly."""
    file_system.create_file(file_name="test_file.txt")

    serialised_file_sys = file_system.model_dump_json()
    deserialised_file_sys = FileSystem.model_validate_json(serialised_file_sys)

    assert file_system.model_dump_json() == deserialised_file_sys.model_dump_json()

    file_system.show(full=True)
