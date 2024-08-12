"""Config file for Sphinx and documentation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("../../src").resolve()))
# Configuration file for the Sphinx documentation builder.

# -- Project information

project = "Tado Async"
copyright = "2024, Erwin Douna"  # noqa: A001
author = "Erwin Douna"

release = "0.1"
version = "0.1.0"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]
autosummary_generate = True

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"
