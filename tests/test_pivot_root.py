#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf
from ctypes import c_char_p

this_file_absdir = os.path.dirname(os.path.abspath(__file__))
procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
sys.path.append(procszoo_mod_dir)
from procszoo.c_functions import *

if __name__ == "__main__":
    euid = os.geteuid()
    if euid != 0:
        printf("need superuser privilege, quit")
        sys.exit(1)
    nscmd="%s/lib/procszoo/try_pivot_root.py" % procszoo_mod_dir
    if os.path.exists(nscmd):
        try:
            spawn_namespaces(nscmd=nscmd)
        except NamespaceRequireSuperuserPrivilege as e:
            printf(e)
            sys.exit(1)
    else:
        printf("'%s': such file does not exist" % nscmd)
