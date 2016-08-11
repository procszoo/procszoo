#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf

procszoo_mod_dir = os.path.abspath("%s/.." % os.path.dirname(__file__))
sys.path.append(procszoo_mod_dir)
from procszoo.utils import *

def demo():
    printf("run by func arg: %d" % os.getpid())

if __name__ == "__main__":
    try:
        spawn_namespaces(func=demo)
    except NamespaceRequireSuperuserPrivilege as e:
        printf(e)
        sys.exit(1)
