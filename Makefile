ifeq ("$(origin V)", "command line")
    Q=
else
    Q=@
endif

PYTHON := /usr/bin/env python
INSTALL_RECORD := install.log

all: build

configure: configure.ac
	$(Q)[ -e configure ] && autoreconf || autoconf
	$(Q)./configure

build: configure build_ext

build_ext:
	$(Q)$(PYTHON) ./setup.py build_ext --inplace

install: all
	$(Q)$(PYTHON) ./setup.py install --record "$(INSTALL_RECORD)"

uninstall:
	$(Q)while read line; do rm -rf "$$line"; done < "$(INSTALL_RECORD)"
	$(Q)rm -f "$(INSTALL_RECORD)"

clean:
	$(Q)rm -rf build
	$(Q)rm -f configure procszoo/c_functions/macros.py
	$(Q)find . -name "*.pyc" | xargs rm -f
	$(Q)find . -name "*~" | xargs rm -f
	$(Q)find . -name "__pycache__" -print0 | xargs -0 rm -rf
	$(Q)rm -rf autom4te.cache config.log config.status

.PHONY: all build clean build_ext install uninstall

