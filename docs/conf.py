project = "collective.webhook"
author = "Asko Soukka"
copyright = "Asko Soukka and contributors"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
]

myst_enable_extensions = [
    "deflist",
]

html_theme = "plone_sphinx_theme"
html_theme_options = {
    "logo": {"text": "collective.webhook"},
    "path_to_docs": "docs",
    "repository_branch": "master",
    "repository_url": "https://github.com/collective/collective.webhook",
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
}

exclude_patterns = ["_build"]
