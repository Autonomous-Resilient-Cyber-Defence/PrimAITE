from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType


def test_file_type():
    """Tests tha the FileSystemFile type is set correctly."""
    file = FileSystemFile(file_size=1.5, file_type=FileSystemFileType.TBD)
    assert file.get_file_type() is FileSystemFileType.TBD


def test_get_file_size():
    """Tests that the file size is being returned properly."""
    file = FileSystemFile(file_size=1.5, file_type=FileSystemFileType.TBD)
    assert file.get_file_size() is 1.5
