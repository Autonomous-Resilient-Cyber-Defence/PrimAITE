from enum import Enum


class FileSystemFileType(str, Enum):
    """Enum used to determine the FileSystemFile type."""

    CSV = ("CSV",)
    DOC = ("DOC",)
    EXE = ("EXE",)
    PDF = ("PDF",)
    TXT = ("TXT",)
    XML = ("XML",)
    ZIP = "ZIP"
