from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType
from primaite.simulator.file_system.file_system_folder import FileSystemFolder


def test_adding_removing_file():
    folder = FileSystemFolder()

    file = FileSystemFile(file_size=10, file_type=FileSystemFileType.TBD)

    folder.add_file(file)
    assert folder.get_folder_size() is 10
    assert len(folder.get_files()) is 1

    folder.remove_file(file_id=file.uuid)
    assert folder.get_folder_size() is 0
    assert len(folder.get_files()) is 0


def test_get_file_by_id():
    folder = FileSystemFolder()

    file = FileSystemFile(file_size=10, file_type=FileSystemFileType.TBD)

    folder.add_file(file)
    assert folder.get_folder_size() is 10
    assert len(folder.get_files()) is 1

    assert folder.get_file(file_id=file.uuid) is file


def test_folder_quarantine_state():
    folder = FileSystemFolder()

    assert folder.quarantine_status() is False

    folder.quarantine()
    assert folder.quarantine_status() is True

    folder.end_quarantine()
    assert folder.quarantine_status() is False
