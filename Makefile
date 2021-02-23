# makefile for qualikiz-pythontools library
PYTHON?=python
PIP?=$(PYTHON) -m pip
ECHO?=$(shell which echo) -e
PRINTF?=$(shell which printf)

# Variables required for release and bugfix options
PROJECT=imaspy
PROJECT_ID=unknown
PACKAGE=imaspy
PACKAGE_HOST=gitlab

# Other variables
SUBDIRS:=

#####################################################

.PHONY: help clean sdist bdist wheel install_package upload_package_to_gitlab install_package_from_gitlab docs tests realclean

help:
	@$(ECHO) "Recipes:"
	@$(ECHO) "  clean                       - remove all build, test, doc, and Python artifacts"
	@$(ECHO) "  sdist                       - build package for source distribution"
	@$(ECHO) "  bdist                       - build package for binary distribution"
	@$(ECHO) "  wheel                       - build package for binary wheel distribution"
	@$(ECHO) "  upload_package_to_gitlab    - build wheel and sdist + upload to GitLab "
	@$(ECHO) "  install_package_from_gitlab - install package from GitLabs simple repository"
	@$(ECHO) "  docs                        - build documentation for package"
	@$(ECHO) "  realclean                   - clean and remove build distributions "
	@$(ECHO) ""
	@$(ECHO) "Environment variables:"
	@$(ECHO) "  PYTHON                      - Python binary to use for commands [default: "$(shell grep -e PYTHON?\= Makefile | cut -d\= -f2)"]"
	@$(ECHO) "  PIP                         - Pip binary to use for commands [default: "$(shell grep -e PIP?\= Makefile | cut -d\= -f2)"]"
	@$(ECHO) "  PYTHONTOOLS_EXTRAS          - Extras to install [default: "$(shell grep -e PYTHONTOOLS_EXTRAS?\= Makefile | cut -d\= -f2)"]"

clean:
	@echo 'Cleaning $(PROJECT)...'
	$(PYTHON) setup.py clean --all
	$(MAKE) -C docs $@

# Build a 'sdist' or 'installable source distribution' with setuptools
# This creates a sdist package installable with pip
# On pip install this will re-compile from source compiled components
sdist:
	@echo 'Building sdist with PYTHON=$(PYTHON)'
	$(PYTHON) setup.py sdist

# Build a 'bdist' or 'installable binary distribution' with setuptools
# This creates a bdist package installable with pip
# This should be pip-installable on the system it was compiled on
# Not recommended to use this! Use wheels instead
bdist:
	@echo 'Building bdist with PYTHON=$(PYTHON)'
	$(PYTHON) setup.py bdist

# Build a 'wheel' or 'installable universial binary distribution' with setuptools
# This creates a wheel that can be used with pip
wheel:
	@echo 'Building wheel with PYTHON=$(PYTHON)'
	$(PYTHON) setup.py bdist_wheel

# Get the current version.
# The name will be generated from git, i.e.
# imaspy-0.1.dev240+g95f5f13.d20200904.tar.gz
# See https://pypi.org/project/setuptools-scm/
# Falls back to `_PYTHONTOOLS_VERSION` env variable if setup.py can't figure it out
# Falls back to 0.0.0 if _that_ does not exist
VERSION_STRING=$(shell $(PYTHON) setup.py --version)
WHEEL_NAME:=$(PACKAGE)-$(VERSION_STRING)-py3-none-any.whl
SDIST_NAME:=$(PACKAGE)-$(VERSION_STRING).tar.gz

IMASPY_TMP_DIR?=install
PYTHON_INSTALL_DIR?=$(IMASPY_TMP_DIR)
# TODO: imas dependency not found by setuptoools
PYTHONTOOLS_EXTRAS?='backends_xarray,test,docs'
install_package: wheel
	@echo [INFO] Installing version '$(VERSION_STRING)'
	@echo [INFO] With extras $(PYTHONTOOLS_EXTRAS)
	@echo [INFO] to $(PYTHON_INSTALL_DIR)
	@echo [INFO] Assuming generated wheel is '$(WHEEL_NAME)'
	@echo [DEBUG] setuptools version=$(shell $(PYTHON) -c "import setuptools; print(setuptools.__version__)")
	@echo [DEBUG] setuptools SCM detected version=$(shell $(PYTHON) -c "from setuptools_scm import get_version; print(get_version(root='.'));")
	@echo [DEBUG] wheel version=$(shell $(PYTHON) -c "import wheel; print(wheel.__version__)")
	pip install dist/$(WHEEL_NAME)[$(PYTHONTOOLS_EXTRAS)] --target=$(PYTHON_INSTALL_DIR) --cache-dir=$(PYTHON_INSTALL_DIR)/pip_cache --upgrade


# You need write permission the the package repository to do this. We use deploy tokens for this
# that are tracked by pip. See https://docs.gitlab.com/ee/user/packages/pypi_repository/
# This involves:
#   - Getting a deploy key for the repository
#   - Setting up your default pip settings with ~/.pypirc
#   - (optional) build an encryped password store with e.g. KGpg
upload_package_to_gitlab: wheel sdist
	$(PYTHON) -m twine upload --verbose --repository $(PACKAGE)_$(PACKAGE_HOST) dist/$(WHEEL_NAME) dist/$(SDIST_NAME)

install_package_from_gitlab:
	$(PIP) install $(PACKAGE)[$(PYTHONTOOLS_EXTRAS)] --extra-index-url https://$(PACKAGE_HOST).com/api/v4/projects/$(PROJECT_ID)/packages/pypi/simple

docs:
	$(MAKE) -C docs html

PYTEST?=pytest
COV_FLAGS?=--cov=$(PACKAGE) --cov-report=term --cov-report=xml:./coverage.xml
JUNIT_FLAGS?=--junit-xml=./junit.xml
PYTEST_MARK?=
PYTEST_FLAGS?=-n auto
tests:
	$(PYTEST) $(PYTEST_FLAGS) $(COV_FLAGS) $(JUNIT_FLAGS) -m "$(PYTEST_MARK)" $(PROJECT)

minitests:
	$(PYTEST) --ids pulse_schedule,ece $(PYTEST_FLAGS) $(COV_FLAGS) $(JUNIT_FLAGS) -m "$(PYTEST_MARK)" $(PROJECT)

realclean: clean
	@echo 'Real cleaning $(PROJECT)...'
	rm -f dist/*
	$(MAKE) -C docs $@

echo_env:
	@echo IMASPY_TMP_DIR=$(IMASPY_TMP_DIR)
	@echo PYTHON_INSTALL_DIR=$(PYTHON_INSTALL_DIR)
