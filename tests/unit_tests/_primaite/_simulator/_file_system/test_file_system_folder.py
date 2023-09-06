from primaite.simulator.file_system.file_system import File
from primaite.simulator.file_system.file_system_folder import Folder
from primaite.simulator.file_system.file_type import FileType


def test_adding_removing_file():
    """Test the adding and removing of a file from a folder."""
    folder = Folder(name="test")

    file = File(name="test_file", size=10, file_type=FileType.DOC)

    folder.add_file(file)
    assert folder.size == 10
    assert len(folder.files) is 1

    folder.remove_file(file)
    assert folder.size == 0
    assert len(folder.files) is 0


def test_remove_non_existent_file():
    """Test the removing of a file that does not exist."""
    folder = Folder(name="test")

    file = File(name="test_file", size=10, file_type=FileType.DOC)
    not_added_file = File(name="fake_file", size=10, file_type=FileType.DOC)

    folder.add_file(file)
    assert folder.size == 10
    assert len(folder.files) is 1

    folder.remove_file(not_added_file)
    assert folder.size == 10
    assert len(folder.files) is 1


def test_get_file_by_id():
    """Test to make sure that the correct file is returned."""
    folder = Folder(name="test")

    file = File(name="test_file", size=10, file_type=FileType.DOC)
    file2 = File(name="test_file_2", size=10, file_type=FileType.DOC)

    folder.add_file(file)
    folder.add_file(file2)
    assert folder.size == 20
    assert len(folder.files) is 2

    assert folder.get_file_by_id(file_id=file.uuid) is file


def test_folder_quarantine_state():
    """Tests the changing of folder quarantine status."""
    folder = Folder(name="test")

    assert folder.quarantine_status() is False

    folder.quarantine()
    assert folder.quarantine_status() is True

    folder.unquarantine()
    assert folder.quarantine_status() is False


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    folder = Folder(name="test")
    file = File(name="test_file", size=10, file_type=FileType.DOC)
    folder.add_file(file)

    serialised_folder = folder.model_dump_json()

    deserialised_folder = Folder.model_validate_json(serialised_folder)

    assert folder.model_dump_json() == deserialised_folder.model_dump_json()
