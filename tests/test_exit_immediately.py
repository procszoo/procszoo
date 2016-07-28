#!/usr/bin/env python
import os
import sys

cwd = os.path.abspath("%s/.." % os.path.dirname(os.path.abspath(__file__)))
sys.path.append("%s" % cwd)
from procszoo.utils import workbench

if __name__ == "__main__":
    workbench.spawn_namespaces(nscmd="./exit_immediately")
