"""
Configuration file for the Sphinx documentation builder.
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(".."))

# Project information
project = "Paddi"
copyright = "2025, Paddi Team"
author = "Paddi Team"
release = "0.1.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "myst_parser",
    "autodoc_pydantic",
]

# Add support for Markdown files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output options
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# MyST parser settings
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_image",
]
