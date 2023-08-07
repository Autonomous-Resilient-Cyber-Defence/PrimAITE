from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType


def test_file_type():
    """Tests tha the FileSystemFile type is set correctly."""
    file = FileSystemFile(item_name="test", file_type=FileSystemFileType.DOC)
    assert file.get_file_type() is FileSystemFileType.DOC


def test_get_file_size():
    """Tests that the file size is being returned properly."""
    file = FileSystemFile(item_name="test", item_size=1.5)
    assert file.get_file_size() == 1.5


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    file = FileSystemFile(item_name="test", item_size=1.5, file_type=FileSystemFileType.DOC)
    serialised_file = file.model_dump_json()
    deserialised_file = FileSystemFile.model_validate_json(serialised_file)

    assert file.model_dump_json() == deserialised_file.model_dump_json()
