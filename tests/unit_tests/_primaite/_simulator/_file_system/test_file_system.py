import pytest

from primaite.simulator.file_system.file_system import File, FileSystem, FileSystemItemHealthStatus, Folder
from primaite.simulator.file_system.file_type import FileType


def test_create_folder_and_file(file_system):
    """Test creating a folder and a file."""
    assert len(file_system.folders) == 1
    file_system.create_folder(folder_name="test_folder")

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
    assert len(file_system.get_folder("root").deleted_files) == 1


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
    assert len(file_system.deleted_folders) == 1


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
    assert len(file_system.get_folder("src_folder").deleted_files) == 0
    assert len(file_system.get_folder("dst_folder").files) == 0

    file_system.move_file(src_folder_name="src_folder", src_file_name="test_file.txt", dst_folder_name="dst_folder")

    assert len(file_system.get_folder("src_folder").files) == 0
    assert len(file_system.get_folder("src_folder").deleted_files) == 1
    assert len(file_system.get_folder("dst_folder").files) == 1
    assert file_system.get_file("dst_folder", "test_file.txt").uuid == original_uuid


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


def test_folder_quarantine_state(file_system):
    """Tests the changing of folder quarantine status."""
    folder = file_system.get_folder("root")

    assert folder.quarantine_status() is False

    folder.quarantine()
    assert folder.quarantine_status() is True

    folder.unquarantine()
    assert folder.quarantine_status() is False


def test_file_corrupt_repair(file_system):
    """Test the ability to corrupt and repair files."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    file.corrupt()

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED

    file.repair()

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_folder_corrupt_repair(file_system):
    """Test the ability to corrupt and repair folders."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    folder.corrupt()

    file = folder.get_file(file_name="test_file.txt")
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED

    folder.repair()

    file = folder.get_file(file_name="test_file.txt")
    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_file_scan(file_system):
    """Test the ability to update visible status."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    file.corrupt()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    file.scan()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPTED


def test_folder_scan(file_system):
    """Test the ability to update visible status."""
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")
    file_system.create_file(file_name="test_file2.txt", folder_name="test_folder")

    file1: File = folder.get_file_by_id(file_uuid=list(folder.files)[1])
    file2: File = folder.get_file_by_id(file_uuid=list(folder.files)[0])

    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.corrupt()

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert folder.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file1.visible_health_status == FileSystemItemHealthStatus.GOOD
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.scan()

    folder.apply_timestep(timestep=0)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file1.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file2.visible_health_status == FileSystemItemHealthStatus.GOOD

    folder.apply_timestep(timestep=1)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file1.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file2.visible_health_status == FileSystemItemHealthStatus.CORRUPTED

    folder.apply_timestep(timestep=2)

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file1.visible_health_status == FileSystemItemHealthStatus.CORRUPTED
    assert file2.visible_health_status == FileSystemItemHealthStatus.CORRUPTED


def test_simulated_file_check_hash(file_system):
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert file.check_hash() is True

    # change simulated file size
    file.sim_size = 0
    assert file.check_hash() is False
    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED


def test_real_file_check_hash(file_system):
    file: File = file_system.create_file(file_name="test_file.txt", folder_name="test_folder", real=True)

    assert file.check_hash() is True

    # change file content
    with open(file.sim_path, "a") as f:
        f.write("get hacked scrub lol xD\n")

    assert file.check_hash() is False
    assert file.health_status == FileSystemItemHealthStatus.CORRUPTED


def test_simulated_folder_check_hash(file_system):
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder")

    assert folder.check_hash() is True

    # change simulated file size
    file = folder.get_file(file_name="test_file.txt")
    file.sim_size = 0
    assert folder.check_hash() is False
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED


def test_real_folder_check_hash(file_system):
    folder: Folder = file_system.create_folder(folder_name="test_folder")
    file_system.create_file(file_name="test_file.txt", folder_name="test_folder", real=True)

    assert folder.check_hash() is True

    # change simulated file size
    file = folder.get_file(file_name="test_file.txt")

    # change file content
    with open(file.sim_path, "a") as f:
        f.write("get hacked scrub lol xD\n")

    assert folder.check_hash() is False
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPTED


@pytest.mark.skip(reason="Skipping until we tackle serialisation")
def test_serialisation(file_system):
    """Test to check that the object serialisation works correctly."""
    file_system.create_file(file_name="test_file.txt")

    serialised_file_sys = file_system.model_dump_json()
    deserialised_file_sys = FileSystem.model_validate_json(serialised_file_sys)

    assert file_system.model_dump_json() == deserialised_file_sys.model_dump_json()
