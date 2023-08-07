from primaite.simulator.file_system.file_system import FileSystem


def test_create_folder_and_file():
    """Test creating a folder and a file."""
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.get_folders()) is 1

    file_system.create_file(file_name="test_file", file_size=10, folder_uuid=folder.uuid)
    assert len(file_system.get_folders()[0].get_files()) is 1
    assert file_system.get_folders()[0].get_files()[0].get_file_name() is "test_file"
    assert file_system.get_folders()[0].get_files()[0].get_file_size() == 10


def test_create_file():
    """Tests that creating a file without a folder creates a folder and sets that as the file's parent."""
    file_system = FileSystem()

    file = file_system.create_file(file_name="test_file", file_size=10)
    assert len(file_system.get_folders()) is 1
    assert file_system.get_folders()[0].get_file(file.uuid) is file


def test_delete_file():
    """Tests that a file can be deleted."""
    file_system = FileSystem()

    file = file_system.create_file(file_name="test_file", file_size=10)
    assert len(file_system.get_folders()) is 1
    assert file_system.get_folders()[0].get_file(file.uuid) is file

    file_system.delete_file(file=file)
    assert len(file_system.get_folders()) is 1
    assert len(file_system.get_folders()[0].get_files()) is 0


def test_delete_folder():
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.get_folders()) is 1

    file_system.delete_folder(folder)
    assert len(file_system.get_folders()) is 0


def test_move_file():
    """Tests the file move function."""
    file_system = FileSystem()
    src_folder = file_system.create_folder(folder_name="test_folder_1")
    assert len(file_system.get_folders()) is 1

    target_folder = file_system.create_folder(folder_name="test_folder_2")
    assert len(file_system.get_folders()) is 2

    file = file_system.create_file(file_name="test_file", file_size=10, folder_uuid=src_folder.uuid)
    assert len(file_system.get_folder_by_id(src_folder.uuid).get_files()) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).get_files()) is 0

    file_system.move_file(file=file, src_folder=src_folder, target_folder=target_folder)

    assert len(file_system.get_folder_by_id(src_folder.uuid).get_files()) is 0
    assert len(file_system.get_folder_by_id(target_folder.uuid).get_files()) is 1


def test_copy_file():
    """Tests the file copy function."""
    file_system = FileSystem()
    src_folder = file_system.create_folder(folder_name="test_folder_1")
    assert len(file_system.get_folders()) is 1

    target_folder = file_system.create_folder(folder_name="test_folder_2")
    assert len(file_system.get_folders()) is 2

    file = file_system.create_file(file_name="test_file", file_size=10, folder_uuid=src_folder.uuid)
    assert len(file_system.get_folder_by_id(src_folder.uuid).get_files()) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).get_files()) is 0

    file_system.copy_file(file=file, src_folder=src_folder, target_folder=target_folder)

    assert len(file_system.get_folder_by_id(src_folder.uuid).get_files()) is 1
    assert len(file_system.get_folder_by_id(target_folder.uuid).get_files()) is 1


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    file_system = FileSystem()
    folder = file_system.create_folder(folder_name="test_folder")
    assert len(file_system.get_folders()) is 1

    file_system.create_file(file_name="test_file", file_size=10, folder_uuid=folder.uuid)
    assert len(file_system.get_folders()[0].get_files()) is 1

    serialised_file_sys = file_system.model_dump_json()
    deserialised_file_sys = FileSystem.model_validate_json(serialised_file_sys)

    assert file_system == deserialised_file_sys
