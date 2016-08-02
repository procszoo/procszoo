#!/usr/bin/env python
import os
import sys
import random
from ctypes import c_char_p

cwd = "%s/.." % os.path.dirname(os.path.abspath(__file__))
sys.path.append("%s" % cwd)
from procszoo.utils import workbench

if __name__ == "__main__":
    euid = os.geteuid()
    if euid != 0:
        print "need superuser privilege, quit"
        sys.exit(1)
    nscmd = nscmd="%s/lib/procszoo/try_pivot_root.py" % cwd
    if os.path.exists(nscmd):
        workbench.spawn_namespaces(nscmd=nscmd)
    else:
        print "'%s': such file does not exist" % nscmd
