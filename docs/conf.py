"""Sphinx configuration for the sphinx-eu-ai-label showcase site."""

from sphinx_eu_ai_label import __version__

project = "sphinx-eu-ai-label"
author = "Kristian Glass"
copyright = f"%Y, {author}"
release = __version__

extensions = [
    "myst_parser",
    "sphinx_eu_ai_label",
]

exclude_patterns = ["_build"]

html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["showcase.css"]
html_theme_options = {
    "description": "EU AI labelling icons for Sphinx",
    "github_user": "doismellburning",
    "github_repo": "sphinx-eu-ai-label",
    "github_button": True,
    "github_type": "star",
}

# Alabaster has no dark mode, so "auto" would show white icons on a white page to readers whose system is in dark mode
eu_ai_label_variant = "black"
