# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

.PHONY: default
default: build

.PHONY: help
help:
	@echo 'General targets:'
	@echo '  build          - build py-utils modules'
	@echo '  clean          - remove build artefacts'
	@echo '  distclean      - perform clean and remove Python virtual env'
	@echo '                   directory with all installed pip modules'
	@echo '  install        - system-wide installation, respects DESTDIR'
	@echo '  uninstall      - uninstall all components, respects DESTDIR'
	@echo
	@echo 'Code linters:'
	@echo '  check          - run `flake8` and `mypy` linters for Python code'
	@echo
	@echo 'Distribution targets:'
	@echo '  rpm            - build release rpm package'
	@echo '  dist           - generate source code distribution archive'

# Globals --------------------------------------------- {{{1
#

SHELL := bash

TOP_SRC_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PY_VENV_DIR := $(TOP_SRC_DIR).py3venv
PYTHON      := python3.6
PY_VENV     := source $(PY_VENV_DIR)/bin/activate
PIP         := $(PY_VENV); pip3.6
SETUP_PY    := $(PY_VENV); $(PYTHON) setup.py
PY3_VERSION := 36
PY3_VERSION_MINOR := $(shell grep -o . <<<$(PY3_VERSION) | tail -n1)

# Build ----------------------------------------------- {{{1
#

.PHONY: build
build: py-utils
	@$(MAKE) --quiet check

.PHONY: py-utils
UTILS_VERSION := $(shell cat VERSION)
UTILS_WHL      := dist/cortx_py_utils-$(UTILS_VERSION)-py3-none-any.whl
py-utils: $(UTILS_WHL)

UTILS_SRC := $(shell find . -type f -regex ".*\.py")
$(UTILS_WHL):
	@$(call _info,Initializing virtual env in $(PY_VENV_DIR) $(UTILS_SRC))
	@$(PYTHON) -m venv $(PY_VENV_DIR) $(wildcard UTILS_SRC)
	@$(call _info,Installing pip modules in virtual env)
	@for f in requirements.txt; do \
	     $(call _log,processing $$f); \
	     $(PIP) install -r $$f; \
	 done
	 #$(UTILS_SRC)
	@$(call _info,Building utils .whl package)
	@($(SETUP_PY) bdist_wheel)

# Clean ----------------------------------------------- {{{1
#

.PHONY: distclean
distclean: clean
	@$(call _info,Cleaning python virtual env and pip modules)
	@if [[ -e $(PY_VENV_DIR) ]]; then \
	     $(call _log,removing $(PY_VENV_DIR)); \
	     rm -rf $(PY_VENV_DIR); \
	 fi

.PHONY: clean
clean: clean-py-utils

.PHONY: clean-py-utils
clean-py-utils:
	@$(call _info,Cleaning utils)
	@for d in build dist cortx_py_utils.egg-info \
	          __pycache__; do \
	     if [[ -e $$d ]]; then \
	         $(call _log,removing $$d); \
	         rm -rf $$d; \
	     fi; \
	 done

# Install --------------------------------------------- {{{1

PREFIX            := opt/seagate/cortx/utils
UTILS_CONF         = $(DESTDIR)/$(PREFIX)/conf
UTILS_EGG_LINK     = $(DESTDIR)/$(PREFIX)/lib/python3.$(PY3_VERSION_MINOR)/site-packages/cortx_py_utils.egg-link
UTILS_INSTALL_CMD  = $(PIP) install --ignore-installed --prefix $(DESTDIR)/$(PREFIX) $(UTILS_WHL:/%=%)

.PHONY: install
install: install-dirs install-utils
	@$(call _info,Installing cortx utils)
	@install requirements.txt $(UTILS_CONF)

.PHONY: install-dirs
install-dirs:
	@$(call _info,Installing cortx utils dirs)
	@install --verbose --directory $(UTILS_CONF)

.PHONY: install-utils
install-utils:
	@$(call _info,Installing cortx utils whl package)
	@$(UTILS_INSTALL_CMD)

.PHONY: install-py-utils-deps
install-py-utils-deps: requirements.txt $(PY_VENV_DIR@$(call _info,Installing py-utils dependencies)
	@$(call _info,Installing py-utils dependencies)
	@$(PIP) install --ignore-installed --prefix $(DESTDIR)/$(PREFIX) -r $<

# Uninstall ------------------------------------------- {{{1
#

# Linters --------------------------------------------- {{{1
.PHONY: check
check: check-utils

.PHONY: check-utils
check-utils: $(PY_VENV_DIR)
	@$(call _info,Checking utils)
	#@$(PY_VENV) &&\
	#   MYPYPATH=../stubs $(PYTHON) setup.py

# Tests ----------------------------------------------- {{{1
#

# RPM ------------------------------------------------- {{{1
#

VERSION   := $(shell cat VERSION)
GITREV     = git$(shell git rev-parse --short HEAD)
DIST_FILE := cortx-py-utils-$(VERSION).tar.gz

RPMBUILD_DIR    := $(HOME)/rpmbuild
RPMBUILD_TOPDIR := $(abspath $(RPMBUILD_DIR))
RPMSOURCES_DIR  := $(RPMBUILD_DIR)/SOURCES
RPMSPECS_DIR    := $(RPMBUILD_DIR)/SPECS

.PHONY: dist
dist: 
	@$(call _info,Generating dist archive)
	@rm -f $(DIST_FILE)
	@git archive -v --prefix=cortx-py-utils/ HEAD -o $(DIST_FILE:.gz=)
	@gzip $(DIST_FILE:.gz=)

.PHONY: __rpm_pre
__rpm_pre: dist
	@$(call _info,Preparing rpmbuild environment)
	@mkdir -v -p $(RPMSOURCES_DIR) $(RPMSPECS_DIR)
	@mv -v $(DIST_FILE) $(RPMSOURCES_DIR)
	@cp -v utils.spec $(RPMSPECS_DIR)
	@chown $$(id -u):$$(id -g) $(RPMSOURCES_DIR)/$(DIST_FILE)
	@chown $$(id -u):$$(id -g) $(RPMSPECS_DIR)/utils.spec

.PHONY: __rpm
__rpm:
	@$(call _info,Building rpm packages)
	@rpmbuild -ba $(RPMSPECS_DIR)/utils.spec \
	          --define "_topdir $(RPMBUILD_TOPDIR)" \
	          --define "u_version $(VERSION)" \
	          --define "u_gitrev $(GITREV)" \
	          $(RPMBUILD_FLAGS)

.PHONY: __rpm_post
__rpm_post:
	@rm -f $(RPMSOURCES_DIR)/$(DIST_FILE) $(RPMSPECS_DIR)/utils.spec

.PHONY: __rpm_srpm
__rpm_srpm:
	@$(call _info,Building source rpm packages)
	@rpmbuild -bs $(RPMSPECS_DIR)/utils.spec \
	          --define "_topdir $(RPMBUILD_TOPDIR)" \
	          --define "u_version $(VERSION)" \
	          --define "u_gitrev $(GITREV)" \
	          $(RPMBUILD_FLAGS)

.PHONY: rpm
rpm:
	@$(MAKE) __rpm_pre
	@$(MAKE) __rpm
	@$(MAKE) __rpm_post

.PHONY: srpm
srpm:
	@$(MAKE) __rpm_pre
	@$(MAKE) __rpm_srpm
	@$(MAKE) __rpm_post

# Functions ------------------------------------------- {{{1
#

# all variations of white and grey colors are invisible on terminals that use
# Solarized colorscheme, cyan seems to be a good compromise here, it looks
# decent on the default black/white terminal, as well as on Solarized
define _info
    if [[ -t 1 ]]; then \
        CYAN=$$(tput bold; tput setaf 6); \
        NC=$$(tput sgr0); \
    fi; \
    echo "$${CYAN}--> $(1)$${NC}"
endef

define _log
    if [[ -t 1 ]]; then \
        YELLOW=$$(tput setaf 3); \
        NC=$$(tput sgr0); \
    fi; \
    echo "$${YELLOW}    $(1)$${NC}"
endef

# vim: textwidth=80 nowrap foldmethod=marker
