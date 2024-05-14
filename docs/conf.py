# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
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
from typing import Any

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
    # "sphinx.ext.autosummary",  # Create summary tables for modules/classes/methods etc
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
nbsphinx_allow_errors = True


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

temp_ignored_notebooks = ["Training-an-RLLib-Agent.ipynb", "Training-an-RLLIB-MARL-System.ipynb"]


def copy_notebooks_to_docs():
    """Copies the notebooks to a directory within docs directory so that they can be included."""
    for notebook in Path("../src/primaite").rglob("*.ipynb"):
        if notebook.name not in temp_ignored_notebooks:
            dest = Path("source") / "notebooks"
            Path(dest).mkdir(parents=True, exist_ok=True)
            shutil.copy2(src=notebook, dst=dest)

    # copy any images
    # TODO


def setup(app: Any):
    """Custom setup for sphinx."""
    copy_notebooks_to_docs()
    app.add_config_value("tokens", {}, True)
    app.connect("source-read", replace_token)
