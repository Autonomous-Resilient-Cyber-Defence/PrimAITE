from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.file_system.file_system_folder import FileSystemFolder


def test_create_folder_and_file():
    """Test creating a folder and a file."""
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) is 1

    file = file_system.create_file(file_name="test_file", size=10, folder_uuid=folder.uuid)
    assert len(file_system.get_folder_by_id(folder.uuid).files) is 1

    assert file_system.get_file_by_id(file.uuid).name is "test_file"
    assert file_system.get_file_by_id(file.uuid).size == 10


def test_create_file():
    """Tests that creating a file without a folder creates a folder and sets that as the file's parent."""
    file_system = FileSystem()

    file = file_system.create_file(file_name="test_file", size=10)
    assert len(file_system.folders) is 1
    assert file_system.get_folder_by_name("root").get_file_by_id(file.uuid) is file


def test_delete_file():
    """Tests that a file can be deleted."""
    file_system = FileSystem()

    file = file_system.create_file(file_name="test_file", size=10)
    assert len(file_system.folders) is 1

    folder_id = list(file_system.folders.keys())[0]
    folder = file_system.get_folder_by_id(folder_id)
    assert folder.get_file_by_id(file.uuid) is file

    file_system.delete_file(file=file)
    assert len(file_system.folders) is 1
    assert len(file_system.get_folder_by_id(folder.uuid).files) is 0


def test_delete_non_existent_file():
    """Tests deleting a non existent file."""
    file_system = FileSystem()

    file = file_system.create_file(file_name="test_file", size=10)
    not_added_file = file_system.create_file(file_name="test_file", size=10)
    assert len(file_system.folders) is 1

    folder_id = list(file_system.folders.keys())[0]
    folder = file_system.get_folder_by_id(folder_id)
    assert folder.get_file_by_id(file.uuid) is file

    file_system.delete_file(file=not_added_file)
    assert len(file_system.folders) is 1
    assert len(file_system.get_folder_by_id(folder.uuid).files) is 1


def test_delete_folder():
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) is 1

    file_system.delete_folder(folder)
    assert len(file_system.folders) is 0


def test_deleting_a_non_existent_folder():
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    not_added_folder = FileSystemFolder(name="fake_folder")
    assert len(file_system.folders) is 1

    file_system.delete_folder(not_added_folder)
    assert len(file_system.folders) is 1


def test_move_file():
    """Tests the file move function."""
    file_system = FileSystem()
    src_folder = file_system.create_folder(folder_name="test_folder_1")
    assert len(file_system.folders) is 1

    target_folder = file_system.create_folder(folder_name="test_folder_2")
    assert len(file_system.folders) is 2

    file = file_system.create_file(file_name="test_file", size=10, folder_uuid=src_folder.uuid)
    assert len(file_system.get_folder_by_id(src_folder.uuid).files) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).files) is 0

    file_system.move_file(file=file, src_folder=src_folder, target_folder=target_folder)

    assert len(file_system.get_folder_by_id(src_folder.uuid).files) is 0
    assert len(file_system.get_folder_by_id(target_folder.uuid).files) is 1


def test_copy_file():
    """Tests the file copy function."""
    file_system = FileSystem()
    src_folder = file_system.create_folder(folder_name="test_folder_1")
    assert len(file_system.folders) is 1

    target_folder = file_system.create_folder(folder_name="test_folder_2")
    assert len(file_system.folders) is 2

    file = file_system.create_file(file_name="test_file", size=10, folder_uuid=src_folder.uuid)
    assert len(file_system.get_folder_by_id(src_folder.uuid).files) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).files) is 0

    file_system.copy_file(file=file, src_folder=src_folder, target_folder=target_folder)

    assert len(file_system.get_folder_by_id(src_folder.uuid).files) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).files) is 1


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.folders) is 1

    file_system.create_file(file_name="test_file", size=10, folder_uuid=folder.uuid)
    assert file_system.get_folder_by_id(folder.uuid) is folder

    serialised_file_sys = file_system.model_dump_json()
    deserialised_file_sys = FileSystem.model_validate_json(serialised_file_sys)

    assert file_system.model_dump_json() == deserialised_file_sys.model_dump_json()
