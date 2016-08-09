#!/usr/bin/env python
import os
import sys

procszoo_mod_dir = os.path.abspath("%s/.." % os.path.dirname(__file__))
sys.path.append(procszoo_mod_dir)
from procszoo.utils import *

if __name__ == "__main__":
    nscmd="%s/lib/procszoo/exit_immediately" % procszoo_mod_dir
    if os.path.exists(nscmd):
        try:
            spawn_namespaces(nscmd=nscmd)
        except NamespaceRequireSuperuserPrivilege as e:
            print(e)
            sys.exit(1)
    else:
        print "'%s': such file does not exist" % nscmd
