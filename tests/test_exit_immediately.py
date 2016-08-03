#!/usr/bin/env python
import os
import sys

procszoo_mod_dir = os.path.abspath("%s/.." % os.path.dirname(__file__))
sys.path.append(procszoo_mod_dir)
from procszoo.utils import workbench

if __name__ == "__main__":
    nscmd="%s/lib/procszoo/exit_immediately" % procszoo_mod_dir
    if os.path.exists(nscmd):
        workbench.spawn_namespaces(nscmd=nscmd)
    else:
        print "'%s': such file does not exist" % nscmd
