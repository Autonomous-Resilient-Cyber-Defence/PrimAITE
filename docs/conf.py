# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
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
    "sphinx.ext.autosummary",  # Create summary tables for modules/classes/methods etc
    "sphinx.ext.intersphinx",  # Link to other project's documentation (see mapping below)
    "sphinx.ext.viewcode",  # Add a link to the Python source code for classes, functions etc.
    "sphinx.ext.todo",
    "sphinx_copybutton",  # Adds a copy button to code blocks
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


def get_notebook_links() -> str:
    """
    Returns a string which will be added to the RST.

    Allows for dynamic addition of notebooks to the documentation.
    """
    notebooks = os.listdir("_static/notebooks/html")

    links = []
    links.append("<ul>")
    for notebook in notebooks:
        if notebook == "notebook_links.html":
            continue
        notebook_link = (
            f'<li><a href="../_static/notebooks/html/{notebook}" target="blank">'
            f"{notebook.replace('.html', '')}"
            f"</a></li>\n"
        )
        links.append(notebook_link)
    links.append("<ul>")

    with open("_static/notebooks/html/notebook_links.html", "w") as html_file:
        html_file.write("".join(links))

    return ":file: ../_static/notebooks/html/notebook_links.html"


def replace_token(app: Any, docname: Any, source: Any):
    """Replaces a token from the list of tokens."""
    result = source[0]
    for key in app.config.tokens:
        result = result.replace(key, app.config.tokens[key])
    source[0] = result


tokens = {
    "{VERSION}": release,
    "{NOTEBOOK_LINKS}": get_notebook_links(),
}  # Token VERSION is replaced by the value of the PrimAITE version in the version file
"""Dict containing the tokens that need to be replaced in documentation."""


def setup(app: Any):
    """Custom setup for sphinx."""
    app.add_config_value("tokens", {}, True)
    app.connect("source-read", replace_token)
