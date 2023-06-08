# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

import furo  # noqa

sys.path.insert(0, os.path.abspath("../"))


# -- Project information -----------------------------------------------------
year = datetime.datetime.now().year
project = "PrimAITE"
copyright = f"Copyright (C) QinetiQ Training and Simulation Ltd 2021 - {year}"
author = "QinetiQ Training and Simulation Ltd"

# The short Major.Minor.Build version
with open("../src/primaite/VERSION", "r") as file:
    version = file.readline()
# The full version, including alpha/beta/rc tags
release = version

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
    "sphinx_code_tabs",  # Enables tabbed code blocks
]


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
