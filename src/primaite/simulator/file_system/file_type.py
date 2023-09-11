from __future__ import annotations

from enum import Enum
from random import choice
from typing import Any


class FileType(Enum):
    """An enumeration of common file types."""

    UNKNOWN = 0
    "Unknown file type."

    # Text formats
    TXT = 1
    "Plain text file."
    DOC = 2
    "Microsoft Word document (.doc)"
    DOCX = 3
    "Microsoft Word document (.docx)"
    PDF = 4
    "Portable Document Format."
    HTML = 5
    "HyperText Markup Language file."
    XML = 6
    "Extensible Markup Language file."
    CSV = 7
    "Comma-Separated Values file."

    # Spreadsheet formats
    XLS = 8
    "Microsoft Excel file (.xls)"
    XLSX = 9
    "Microsoft Excel file (.xlsx)"

    # Image formats
    JPEG = 10
    "JPEG image file."
    PNG = 11
    "PNG image file."
    GIF = 12
    "GIF image file."
    BMP = 13
    "Bitmap image file."

    # Audio formats
    MP3 = 14
    "MP3 audio file."
    WAV = 15
    "WAV audio file."

    # Video formats
    MP4 = 16
    "MP4 video file."
    AVI = 17
    "AVI video file."
    MKV = 18
    "MKV video file."
    FLV = 19
    "FLV video file."

    # Presentation formats
    PPT = 20
    "Microsoft PowerPoint file (.ppt)"
    PPTX = 21
    "Microsoft PowerPoint file (.pptx)"

    # Web formats
    JS = 22
    "JavaScript file."
    CSS = 23
    "Cascading Style Sheets file."

    # Programming languages
    PY = 24
    "Python script file."
    C = 25
    "C source code file."
    CPP = 26
    "C++ source code file."
    JAVA = 27
    "Java source code file."

    # Compressed file types
    RAR = 28
    "RAR archive file."
    ZIP = 29
    "ZIP archive file."
    TAR = 30
    "TAR archive file."
    GZ = 31
    "Gzip compressed file."

    # Database file types
    DB = 32
    "Generic DB file. Used by sqlite3."

    @classmethod
    def _missing_(cls, value: Any) -> FileType:
        return cls.UNKNOWN

    @classmethod
    def random(cls) -> FileType:
        """
        Returns a random FileType.

        :return: A random FileType.
        """
        return choice(list(FileType))

    @property
    def default_size(self) -> int:
        """
        Get the default size of the FileType in bytes.

        Returns 0 if a default size does not exist.
        """
        size = file_type_sizes_bytes[self]
        return size if size else 0


def get_file_type_from_extension(file_type_extension: str) -> FileType:
    """
    Get a FileType from a file type extension.

    If a matching extension does not exist, FileType.UNKNOWN is returned.

    :param file_type_extension: A file type extension.
    :return: A file type extension.
    """
    try:
        return FileType[file_type_extension.upper()]
    except KeyError:
        return FileType.UNKNOWN


file_type_sizes_bytes = {
    FileType.UNKNOWN: 0,
    FileType.TXT: 4096,
    FileType.DOC: 51200,
    FileType.DOCX: 30720,
    FileType.PDF: 102400,
    FileType.HTML: 15360,
    FileType.XML: 10240,
    FileType.CSV: 15360,
    FileType.XLS: 102400,
    FileType.XLSX: 25600,
    FileType.JPEG: 102400,
    FileType.PNG: 40960,
    FileType.GIF: 30720,
    FileType.BMP: 307200,
    FileType.MP3: 5120000,
    FileType.WAV: 25600000,
    FileType.MP4: 25600000,
    FileType.AVI: 51200000,
    FileType.MKV: 51200000,
    FileType.FLV: 15360000,
    FileType.PPT: 204800,
    FileType.PPTX: 102400,
    FileType.JS: 10240,
    FileType.CSS: 5120,
    FileType.PY: 5120,
    FileType.C: 5120,
    FileType.CPP: 10240,
    FileType.JAVA: 10240,
    FileType.RAR: 1024000,
    FileType.ZIP: 1024000,
    FileType.TAR: 1024000,
    FileType.GZ: 819200,
    FileType.DB: 15360000,
}
