import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "BounceRL"
copyright = "2025, William Henning"
author = "William Henning"
release = "0.0.41"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]

# Theme is inspired by Farama Foundation's Celshast theme:
#   https://github.com/Farama-Foundation/Celshast
html_css_files = [
    "theme.css",
]
html_theme_options = {
    "light_css_variables": {
        "sidebar-caption-font-size": "110%",
        "sidebar-item-font-size": "90%",
        "sidebar-item-border-radius": "8px",
        "sidebar-tree-space-horizontal": "0.5rem",
        "toc-font-size": "var(--font-size--small)",
        "color-api-pre-name": "#144fff",
        "color-api-name": "#144fff",
        "color-sidebar-link-text--top-level": "#000000",
        "color-sidebar-caption-text": "#4a4a4a",
        "color-sidebar-item-background--current": "#eeeeee",
        "color-sidebar-item-background--hover": "#e7e7e7",
        "color-toc-item-text--active": "var(--color-toc-item-text)",
    },
    "dark_css_variables": {
        "color-api-pre-name": "#daba8e",
        "color-api-name": "#daba8e",
        "color-sidebar-link-text--top-level": "#ffffff",
        "color-sidebar-caption-text": "#919191",
        "color-sidebar-item-background--current": "#252525",
        "color-sidebar-item-background--hover": "#2b2b2b",
        "color-toc-item-text": "#d7d7d7",
        "color-toc-item-text--active": "var(--color-toc-item-text)",
    },
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
