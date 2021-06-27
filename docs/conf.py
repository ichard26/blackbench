# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys

try:
    import blackbench
except ImportError:
    print(
        "ERROR: building the documentation requires an importable installation of"
        " blackbench."
    )
    sys.exit(1)

# -- Project information -----------------------------------------------------

project = "blackbench"
copyright = "2021, Richard Si et al."
author = "Richard Si"
release = version = blackbench.__version__

# -- General configuration ---------------------------------------------------

needs_sphinx = "4.0.0"
needs_extensions = {"myst_parser": "0.15.1"}

extensions = [
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinx_panels",
]

todo_include_todos = True

exclude_patterns = ["build", "_build"]

myst_heading_anchors = 3
myst_enable_extensions = [
    "deflist",
]

extlinks = {
    "pypi": ("https://pypi.org/project/%s/", ""),
}

intersphinx_mapping = {
    "https://docs.python.org/3/": None,
    "https://pyperf.readthedocs.io/en/stable": None,
}

highlight_language = "none"

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = f"Blackbench {release}"
html_favicon = "static/ichard26-favicon.png"
