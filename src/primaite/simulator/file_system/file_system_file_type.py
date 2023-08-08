from enum import Enum


class FileSystemFileType(str, Enum):
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


file_type_sizes_KB = {
    FileSystemFileType.UNKNOWN: 0,
    FileSystemFileType.TXT: 4,
    FileSystemFileType.DOC: 50,
    FileSystemFileType.DOCX: 30,
    FileSystemFileType.PDF: 100,
    FileSystemFileType.HTML: 15,
    FileSystemFileType.XML: 10,
    FileSystemFileType.CSV: 15,
    FileSystemFileType.XLS: 100,
    FileSystemFileType.XLSX: 25,
    FileSystemFileType.JPEG: 100,
    FileSystemFileType.PNG: 40,
    FileSystemFileType.GIF: 30,
    FileSystemFileType.BMP: 300,
    FileSystemFileType.MP3: 5000,
    FileSystemFileType.WAV: 25000,
    FileSystemFileType.MP4: 25000,
    FileSystemFileType.AVI: 50000,
    FileSystemFileType.MKV: 50000,
    FileSystemFileType.FLV: 15000,
    FileSystemFileType.PPT: 200,
    FileSystemFileType.PPTX: 100,
    FileSystemFileType.JS: 10,
    FileSystemFileType.CSS: 5,
    FileSystemFileType.PY: 5,
    FileSystemFileType.C: 5,
    FileSystemFileType.CPP: 10,
    FileSystemFileType.JAVA: 10,
    FileSystemFileType.RAR: 1000,
    FileSystemFileType.ZIP: 1000,
    FileSystemFileType.TAR: 1000,
    FileSystemFileType.GZ: 800,
}
