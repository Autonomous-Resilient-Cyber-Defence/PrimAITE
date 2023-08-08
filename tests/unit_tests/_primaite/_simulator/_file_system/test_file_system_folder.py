from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType
from primaite.simulator.file_system.file_system_folder import FileSystemFolder


def test_adding_removing_file():
    """Test the adding and removing of a file from a folder."""
    folder = FileSystemFolder(name="test")

    file = FileSystemFile(name="test_file", size=10, file_type=FileSystemFileType.DOC)

    folder.add_file(file)
    assert folder.size == 10
    assert len(folder.files) is 1

    folder.remove_file(file)
    assert folder.size == 0
    assert len(folder.files) is 0


def test_remove_non_existent_file():
    """Test the removing of a file that does not exist."""
    folder = FileSystemFolder(name="test")

    file = FileSystemFile(name="test_file", size=10, file_type=FileSystemFileType.DOC)
    not_added_file = FileSystemFile(name="fake_file", size=10, file_type=FileSystemFileType.DOC)

    folder.add_file(file)
    assert folder.size == 10
    assert len(folder.files) is 1

    folder.remove_file(not_added_file)
    assert folder.size == 10
    assert len(folder.files) is 1


def test_get_file_by_id():
    """Test to make sure that the correct file is returned."""
    folder = FileSystemFolder(name="test")

    file = FileSystemFile(name="test_file", size=10, file_type=FileSystemFileType.DOC)
    file2 = FileSystemFile(name="test_file_2", size=10, file_type=FileSystemFileType.DOC)

    folder.add_file(file)
    folder.add_file(file2)
    assert folder.size == 20
    assert len(folder.files) is 2

    assert folder.get_file_by_id(file_id=file.uuid) is file


def test_folder_quarantine_state():
    """Tests the changing of folder quarantine status."""
    folder = FileSystemFolder(name="test")

    assert folder.quarantine_status() is False

    folder.quarantine()
    assert folder.quarantine_status() is True

    folder.end_quarantine()
    assert folder.quarantine_status() is False


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    folder = FileSystemFolder(name="test")
    file = FileSystemFile(name="test_file", size=10, file_type=FileSystemFileType.DOC)
    folder.add_file(file)

    serialised_folder = folder.model_dump_json()

    deserialised_folder = FileSystemFolder.model_validate_json(serialised_folder)

    assert folder.model_dump_json() == deserialised_folder.model_dump_json()
