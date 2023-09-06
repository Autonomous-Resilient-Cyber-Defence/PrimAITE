from primaite.simulator.file_system.file_system import File
from primaite.simulator.file_system.file_type import FileType


def test_file_type():
    """Tests tha the File type is set correctly."""
    file = File(name="test", file_type=FileType.DOC)
    assert file.file_type is FileType.DOC


def test_get_size():
    """Tests that the file size is being returned properly."""
    file = File(name="test", size=1.5)
    assert file.size == 1.5


def test_serialisation():
    """Test to check that the object serialisation works correctly."""
    file = File(name="test", size=1.5, file_type=FileType.DOC)
    serialised_file = file.model_dump_json()
    deserialised_file = File.model_validate_json(serialised_file)

    assert file.model_dump_json() == deserialised_file.model_dump_json()
