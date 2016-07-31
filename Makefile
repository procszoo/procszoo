all: configure
	./configure
configure: configure.ac
	[ -e configure ] && autoreconf || autoconf
clean:
	rm -f configure procszoo/syscall_*.py
	find . -name "*.pyc" | xargs rm -f
	find . -name "*~" | xargs rm -f	
	rm -rf autom4te.cache config.log config.status
