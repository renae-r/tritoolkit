# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import doctest
import inspect
import logging as pylogging

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import shutil
import subprocess
import sys

from sphinx.util import logging

sys.path.append(os.path.abspath("../../src"))
import tritoolkit

sys.path.insert(0, os.path.abspath("../../src/tritoolkit"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "tritoolkit"
copyright = "2023, Renae Rodgers"
author = "Renae Rodgers"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",  # N.B. napoleon must be before autodocs_typehints
    "sphinx_autodoc_typehints",
    # "sphinx.ext.linkcode",  # link to github, see linkcode_resolve() below
    "sphinx_copybutton",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# copy CONTRIBUTING.md docs into source directory
root_dir = os.path.dirname(__file__)
shutil.copyfile(
    os.path.join(root_dir, "..", "..", "CONTRIBUTING.md"),
    os.path.join(root_dir, "CONTRIBUTING.md"),
)

templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

exclude_patterns = []

autoclass_content = "both"

autodoc_default_options = {
    "undoc-members": False,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_title = "tritoolkit"
html_theme = "furo"
html_static_path = ["_static"]

tml_css_files = ["default.css"]

rst_prolog = """
.. role:: red
.. role:: green
"""

autosummary_generate = True
autosummary_filename_map = {}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://docs.scipy.org/doc/numpy/", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable/", None),
}
