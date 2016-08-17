#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf

try:
    from procszoo.c_functions import *
except ImportError:
    this_file_absdir = os.path.dirname(os.path.abspath(__file__))
    procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
    sys.path.append(procszoo_mod_dir)
    from procszoo.c_functions import *

def demo():
    printf("run by func arg: %d" % os.getpid())

if __name__ == "__main__":
    try:
        spawn_namespaces(func=demo)
    except NamespaceRequireSuperuserPrivilege as e:
        printf(e)
        sys.exit(1)
