# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import shutil
import sys
from pathlib import Path
from typing import Any, List, Optional

import furo  # noqa

sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------
year = datetime.datetime.now().year
project = "PrimAITE"
copyright = f"Copyright (C) Defence Science and Technology Laboratory UK 2021 - {year}"
author = "Defence Science and Technology Laboratory UK"

# The short Major.Minor.Build version
with open("../src/primaite/VERSION", "r") as file:
    version = file.readline()
# The full version, including alpha/beta/rc tags
release = version

# set global variables
rst_prolog = f"""
.. |VERSION| replace::  {release}
"""

html_title = f"{project} v{release} docs"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # Core Sphinx library for auto html doc generation from docstrings
    "sphinx.ext.autosummary",  # Create summary tables for modules/classes/methods etc
    "sphinx.ext.intersphinx",  # Link to other project's documentation (see mapping below)
    "sphinx.ext.viewcode",  # Add a link to the Python source code for classes, functions etc.
    "sphinx.ext.todo",
    "sphinx_copybutton",  # Adds a copy button to code blocks
    "nbsphinx",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {"globaltoc_collapse": True, "globaltoc_maxdepth": 2}
html_copy_source = False
nbsphinx_allow_errors = False  # set to True to take shortcuts
html_scaled_image_link = False

# make some stuff easier to read
nbsphinx_prolog = """
.. raw:: html

    <style>
        .stderr {
            color: #000 !important
        }
    </style>
"""


def replace_token(app: Any, docname: Any, source: Any):
    """Replaces a token from the list of tokens."""
    result = source[0]
    for key in app.config.tokens:
        result = result.replace(key, app.config.tokens[key])
    source[0] = result


tokens = {
    "{VERSION}": release,
}  # Token VERSION is replaced by the value of the PrimAITE version in the version file
"""Dict containing the tokens that need to be replaced in documentation."""


def notebook_assets(ignored_files: Optional[List[str]] = [], include_file_types: Optional[List[str]] = []) -> Any:
    """
    Creates a function to be used with `shutil.copytree`'s `ignore` parameter.

    :param ignored_files: A list of specific file names to ignore. If a file in the directory matches one of these
    names, it will be excluded from the copy process.
    :type ignored_files: Optional[List[str]]
    :param include_file_types: A list of file extensions to include in the copy process. Files that do not match these
    extensions will be excluded. If this list is empty, all files will be excluded, effectively copying only
    directories.
    :type include_file_types: Optional[List[str]]
    """

    def ignore_items(directory: List[str], contents: List[str]) -> List[str]:
        """
        Determines which files and directories should be ignored during the copy process.

        :param directory: The directory being copied.
        :type directory: str
        :param contents: A list of contents in the directory.
        :type contents: List[str]
        :return: A list of items to exclude from the copy process.
        :rtype: List[str]
        """
        exclude_items = []

        for item in contents:
            if item in ignored_files:
                exclude_items.append(item)
                continue

            if len(include_file_types) > 0:
                if not any(item.lower().endswith(ext.lower()) for ext in include_file_types) and os.path.isdir(item):
                    exclude_items.append(item)
            else:
                # if we dont specify which files to include, exclude everything
                exclude_items.append(item)

        # exclude files but not directories
        return [path for path in exclude_items if not (Path(directory) / path).is_dir()]

    return ignore_items


def copy_notebooks_to_docs() -> Any:
    """
    Incredibly over-engineered method that copies the notebooks and its assets to a directory within the docs directory.

    This allows developers to create new notebooks without having to worry about updating documentation when
    a new notebook is included within PrimAITE.
    """
    notebook_asset_types = [".ipynb", ".png", ".svg"]
    notebook_directories = []

    # find paths where notebooks are contained
    for notebook in Path("../src/primaite").rglob("*.ipynb"):
        # add parent path to notebook directory if not already added
        if notebook.parent not in notebook_directories:
            notebook_directories.append(notebook.parent)

    # go through the notebook directories and copy the notebooks and extra assets
    for notebook_parent in notebook_directories:
        shutil.copytree(
            src=notebook_parent,
            dst=Path("source") / "notebooks" / notebook_parent.name,
            ignore=notebook_assets(include_file_types=notebook_asset_types),
            dirs_exist_ok=True,
        )


def suppress_log_output():
    """Sets the log level while building the documentation."""
    from primaite import _FILE_HANDLER, _LOGGER, _STREAM_HANDLER

    log_level = "WARN"

    _LOGGER.setLevel(log_level)
    _STREAM_HANDLER.setLevel(log_level)
    _FILE_HANDLER.setLevel(log_level)


def setup(app: Any):
    """Custom setup for sphinx."""
    suppress_log_output()
    copy_notebooks_to_docs()
    app.add_config_value("tokens", {}, True)
    app.connect("source-read", replace_token)
