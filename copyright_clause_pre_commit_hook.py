# -*- coding: utf-8 -*-
import datetime
import sys
from pathlib import Path

# Constants
CURRENT_YEAR = datetime.date.today().year
COPYRIGHT_PY_STR = f"# © Crown-owned copyright {CURRENT_YEAR}, Defence Science and Technology Laboratory UK"
COPYRIGHT_RST_LINES = [
    ".. only:: comment",
    "",
    f"    © Crown-owned copyright {CURRENT_YEAR}, Defence Science and Technology Laboratory UK",
]
PATHS = {Path("./src"), Path("./tests"), Path("./docs"), Path("./benchmark")}
EXTENSIONS = {".py", ".rst"}


def _is_copyright_line(line: str) -> bool:
    """
    Check if a line is a copyright line.

    :param line: The line to check.
    :return: True if the line is a copyright line, False otherwise.
    """
    return line.startswith("#") and "copyright" in line.lower()


def _is_rst_copyright_lines(lines: list) -> bool:
    """
    Check if the lines match the RST copyright format.

    :param lines: The lines to check.
    :return: True if the lines match the RST copyright format, False otherwise.
    """
    return len(lines) >= 3 and lines[0] == ".. only:: comment" and "copyright" in lines[2].lower()


def process_py_file(file_path: Path) -> bool:
    """
    Process a Python file to check and add/update the copyright clause.

    :param file_path: The path to the file to check and update.
    :return: True if the file was modified, False otherwise.
    """
    modified = False
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)  # Keep line endings

        if lines and _is_copyright_line(lines[0]):
            if lines[0].strip() != COPYRIGHT_PY_STR:
                lines[0] = COPYRIGHT_PY_STR + "\n"
                modified = True
                print(f"Updated copyright clause in {file_path}")
        else:
            lines.insert(0, COPYRIGHT_PY_STR + "\n")
            modified = True
            print(f"Added copyright clause to {file_path}")

        if modified:
            file_path.write_text("".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
        return False

    return modified


def process_rst_file(file_path: Path) -> bool:
    """
    Process an RST file to check and add/update the copyright clause.

    :param file_path: The path to the file to check and update.
    :return: True if the file was modified, False otherwise.
    """
    modified = False
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)  # Keep line endings

        existing_block = any(".. only:: comment" in line for line in lines)

        if existing_block:
            # Check if the block is correct
            for i, line in enumerate(lines):
                if line.strip() == ".. only:: comment":
                    if lines[i : i + 3] != [
                        COPYRIGHT_RST_LINES[0] + "\n",
                        COPYRIGHT_RST_LINES[1] + "\n",
                        COPYRIGHT_RST_LINES[2] + "\n",
                    ]:
                        # Update the incorrect block
                        lines[i : i + 3] = [
                            COPYRIGHT_RST_LINES[0] + "\n",
                            COPYRIGHT_RST_LINES[1] + "\n",
                            COPYRIGHT_RST_LINES[2] + "\n",
                        ]
                        modified = True
                        print(f"Updated copyright clause in {file_path}")
                    break
        else:
            # Insert new copyright block
            lines = [line + "\n" for line in COPYRIGHT_RST_LINES] + ["\n"] + lines
            modified = True
            print(f"Added copyright clause to {file_path}")

        if modified:
            file_path.write_text("".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
        return False

    return modified


def process_file(file_path: Path) -> bool:
    """
    Check if a file has the correct copyright clause and add or update it if necessary.

    :param file_path: The path to the file to check and update.
    :return: True if the file was modified, False otherwise.
    """
    if file_path.suffix == ".py":
        return process_py_file(file_path)
    elif file_path.suffix == ".rst":
        return process_rst_file(file_path)
    return False


def main() -> int:
    """
    Main function to walk through the root directories, check files, and update the copyright clause.

    :return: 1 if any file was modified, 0 otherwise.
    """
    files_checked = 0
    files_modified = 0
    any_file_modified = False
    for path in PATHS:
        for file_path in path.rglob("*"):
            if file_path.suffix in EXTENSIONS:
                files_checked += 1
                if process_file(file_path):
                    files_modified += 1
                    any_file_modified = True

    if any_file_modified:
        print(f"Files Checked: {files_checked}. Files Modified: {files_modified}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
