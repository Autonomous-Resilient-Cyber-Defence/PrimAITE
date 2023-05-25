# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
import datetime
import furo
sys.path.insert(0, os.path.abspath("../"))


# -- Project information -----------------------------------------------------
year = datetime.datetime.now().year
project = "primaite"
copyright = f"Copyright (C) QinetiQ Training and Simulation Ltd 2021 - {year}"
author = "QinetiQ Training and Simulation Ltd"

# The short Major.Minor.Build version
with open("../src/primaite/VERSION", "r") as file:
    version = file.readline()
# The full version, including alpha/beta/rc tags
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
