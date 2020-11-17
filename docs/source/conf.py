"""
Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys
import datetime
from urllib.parse import (
    urljoin,
)

# Sphinx extention to format xarray/pandas summaries
import sphinx_autosummary_accessors

from jinja2.defaults import DEFAULT_FILTERS

from pkg_resources import parse_version as V

import imaspy


print("python exec:", sys.executable)
print("sys.path:", sys.path)

# -- Project information -----------------------------------------------------
# The documented project’s name
project = src_project = PROJECT = "IMASPy"

# PROJECT_ID=10189354
PACKAGE = "imaspy"
PACKAGE_HOST = "gitlab"
src_group = GROUP = "KLIMEX"

# A copyright statement in the style '2008, Author Name'.
copyright = f"2016-{datetime.datetime.now().year}, Karel van de Plassche (DIFFER)"
# The author name(s) of the document
author = "Karel van de Plassche (DIFFER)"
src_host = "gitlab.com"

# Parse urls here for convenience, to be re-used
# gitlab imaspy folder
repository_url = f"https://{src_host}/{src_group}/{src_project}/"
blob_url = urljoin(repository_url, "-/blob/master/")
issue_url = urljoin(repository_url, "-/issues/")
mr_url = urljoin(repository_url, "-/merge_requests/")

# JINTRAC docs
jintrac_sphinx = "https://users.euro-fusion.org/pages/data-cmg/wiki/"

# netCDF4 docs
netcdf4_docs = "https://unidata.github.io/netcdf4-python/netCDF4/index.html"

# ITER docs
iter_projects = "https://git.iter.org/projects/"
imas_site = urljoin(iter_projects, "IMAS/")
imex_site = urljoin(iter_projects, "IMEX/")
al_cython_url = urljoin(imas_site, "repos/al-cython/")
al_python_hli_url = urljoin(imas_site, "repos/al-python/")
al_python_lib_url = urljoin(imas_site, "repos/al-python-lib/")
issue_url = jira_url = "https://jira.iter.org/browse/"

# Configuration of sphinx.ext.extlinks
# See https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
# unique name: (base URL, label prefix)
extlinks = {
    "src": (blob_url + "%s", f"{src_group}/{src_project}/"),
    "issue": (issue_url + "%s", None),
    "merge": (mr_url + "%s", "!"),
    "jintrac": (jintrac_sphinx + "%s", "jintrac pages "),
    "netcdf4": (netcdf4_docs + "%s", "netcdf4 "),
    "al_cython": (al_cython_url + "%s", "al_cython "),
    "al_hli": (al_python_hli_url + "%s", "al_hli"),
    "al_lib": (al_python_lib_url + "%s", "al_lib"),
    "pypa": ("https://packaging.python.org/%s", None),
}

full_version = V(imaspy.__version__)

# version: The major project version, used as the replacement for |version|.
#   For example, for the Python documentation, this may be something like 2.6.
version = full_version.base_version

# release: The full project version, used as the replacement for |release| and
#   e.g. in the HTML templates. For example, for the Python documentation, this
#   may be something like 2.6.0rc1
release = str(full_version)


# -- General configuration ---------------------------------------------------
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # To auto-generate docs from Python docstrings
    "sphinx.ext.todo",  # nature theme
    "sphinx.ext.githubpages",  # nature theme
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    "sphinx.ext.intersphinx",  # Generate links to other documentation files
    # 'sphinx.ext.coverage',  # numpy
    # 'sphinx.ext.doctest',  # numpy
    "sphinx.ext.autosummary",  # For summarizing autodoc-generated files
    "sphinx.ext.extlinks",  # For shortening internal links
    "sphinx.ext.graphviz",  # Draw Graphs in docs
    # 'sphinx.ext.ifconfig',  # numpy
    # 'matplotlib.sphinxext.plot_directive',  # numpy
    # 'IPython.sphinxext.ipythoGn_console_highlighting',  # numpy
    # 'IPython.sphinxext.ipython_directive',  # numpy
    "sphinx.ext.mathjax",  # Render math with mathjax
    "sphinx_rtd_theme",  # Theme
    "recommonmark",  # For markdown support, does not support 'full' CommonMark syntax (yet)!
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates", sphinx_autosummary_accessors.templates_path]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The suffix of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%Y-%m-%d"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {"logo_only": True}

# Add any paths that contain custom themes here, relative to this directory.
# html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# '<project> v<release> documentation'.
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/dataset-diagram-logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
# html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = today_fmt

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, 'Created using Sphinx' is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, '(C) Copyright ...' is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. '.xhtml').
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "imaspy_doc"


# -- Extension configuration -------------------------------------------------
# from recommonmark.transform import AutoStructify

# app setup hook
# def setup(app):
#    # add a config value for `ifconfig` directives
#    app.add_config_value('python_version_major', str(sys.version_info.major), 'env')
#    app.add_lexer('NumPyC', NumPyLexer)
#    app.add_config_value('recommonmark_config', {
#        #'url_resolver': lambda url: 'http://' + url,#  a function that maps a existing relative position in the document to a http link
#        'enable_auto_toc_tree': True,  # whether enable Auto Toc Tree feature.
#        'auto_toc_tree_section': 'Contents',  # when enabled, Auto Toc Tree will only be enabled on section that matches the title.
#        'enable_math': True,  # whether enable Math Formula
#        'enable_inline_math': True,  # whether enable Inline Math
#        'enable_eval_rst': False,  # whether Embed reStructuredText is enabled.
#        'enable_auto_doc_ref': None,  # Depracated
#    }, True)
#    app.add_transform(AutoStructify)


# Configuration of sphinx.ext.autodoc
# https://www.sphinx-doc.org/en/master/usage/quickstart.html#autodoc
# autodoc_typehints = "none" #xarray

# Configuration of sphinx.ext.autosummary
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html
autosummary_generate = True

# Configuration of recommonmark
# See https://www.sphinx-doc.org/en/master/usage/markdown.html

# Configuration of sphinx.ext.napoleon
# Support for NumPy and Google style docstrings
# See https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
# napoleon_google_docstring = True
# napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
# napoleon_include_special_with_doc = True
# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False
# napoleon_use_ivar = False
# napoleon_use_param = True
napoleon_use_keyword = True  # Use the "Keyword Args" syntax
# napoleon_use_rtype = True
napoleon_type_aliases = {
    # general terms
    "sequence": ":term:`sequence`",
    "iterable": ":term:`iterable`",
    "callable": ":py:func:`callable`",
    "dict_like": ":term:`dict-like <mapping>`",
    "dict-like": ":term:`dict-like <mapping>`",
    "mapping": ":term:`mapping`",
    "file-like": ":term:`file-like <file-like object>`",
    # special terms
    # 'same type as caller': '*same type as caller*',  # does not work, yet
    # 'same type as values': '*same type as values*',  # does not work, yet
    # stdlib type aliases
    "MutableMapping": "~collections.abc.MutableMapping",
    "sys.stdout": ":obj:`sys.stdout`",
    "timedelta": "~datetime.timedelta",
    "string": ":class:`string <str>`",
    # numpy terms
    "array_like": ":term:`array_like`",
    "array-like": ":term:`array-like <array_like>`",
    "scalar": ":term:`scalar`",
    "array": ":term:`array`",
    "hashable": ":term:`hashable <name>`",
    # matplotlib terms
    "color-like": ":py:func:`color-like <matplotlib.colors.is_color_like>`",
    "matplotlib colormap name": ":doc:matplotlib colormap name <Colormap reference>",
    "matplotlib axes object": ":py:class:`matplotlib axes object <matplotlib.axes.Axes>`",
    "colormap": ":py:class:`colormap <matplotlib.colors.Colormap>`",
    # objects without namespace
    "DataArray": "~xarray.DataArray",
    "Dataset": "~xarray.Dataset",
    "Variable": "~xarray.Variable",
    "ndarray": "~numpy.ndarray",
    "MaskedArray": "~numpy.ma.MaskedArray",
    "dtype": "~numpy.dtype",
    "ComplexWarning": "~numpy.ComplexWarning",
    "Index": "~pandas.Index",
    "MultiIndex": "~pandas.MultiIndex",
    "CategoricalIndex": "~pandas.CategoricalIndex",
    "TimedeltaIndex": "~pandas.TimedeltaIndex",
    "DatetimeIndex": "~pandas.DatetimeIndex",
    "Series": "~pandas.Series",
    "DataFrame": "~pandas.DataFrame",
    "Categorical": "~pandas.Categorical",
    "Path": "~~pathlib.Path",
    # objects with abbreviated namespace (from pandas)
    "pd.Index": "~pandas.Index",
    "pd.NaT": "~pandas.NaT",
}  # TODO: From xarray, improve!

# From xarray, huh?
# napoleon_preprocess_types = True #From xarray, not in docs
# numpydoc_class_members_toctree = True
# numpydoc_show_class_members = False

# Configuration of sphinx.ext.intersphinx
# See https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "numba": ("https://numba.pydata.org/numba-doc/latest", None),
    "matplotlib": ("https://matplotlib.org", None),
    "xarray": ("http://xarray.pydata.org/en/stable/", None),
    "dask": ("https://docs.dask.org/en/latest", None),
    "cython": ("https://cython.readthedocs.io/", None),
    "gitpython": ("https://gitpython.readthedocs.io/en/stable", None),
    # "netcdf4": ("https://unidata.github.io/netcdf4-python/", None),  # netcdf4 does not have an intersphinx mapping
    # "jintrac": ("https://users.euro-fusion.org/pages/data-cmg/wiki/", None) Behind password, so cannot link there
}

# Configuration of sphinx.ext.graphviz
# See https://www.sphinx-doc.org/en/master/usage/extensions/graphviz.html

# Configuration of sphinx.ext.mathjax
# See https://www.sphinx-doc.org/en/master/usage/extensions/math.html#module-sphinx.ext.mathjax

def escape_underscores(string):
    return string.replace("_", r"\_")


def setup(app):
    DEFAULT_FILTERS["escape_underscores"] = escape_underscores
