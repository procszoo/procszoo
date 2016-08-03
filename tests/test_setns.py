#!/usr/bin/env python
import os
import sys
import random

procszoo_mod_dir = os.path.abspath("%s/.." % os.path.dirname(__file__))
sys.path.append(procszoo_mod_dir)
from procszoo.utils import workbench

if __name__ == "__main__":
    if "setns" not in workbench.show_available_c_functions():
        print "setns func unavailable, quit"
        sys.exit(1)
    ns_bind_dir = "/tmp/ns"
    nscmd="%s/lib/procszoo/exit_immediately" % procszoo_mod_dir
    workbench.spawn_namespaces(ns_bind_dir=ns_bind_dir, nscmd=nscmd)
    pid = os.fork()
    if pid == -1:
        raise RuntimeError("failed to do a fork")
    if pid == 0:
        workbench.setns(path="/tmp/ns/net", namespace="net")
        os.system("ifconfig -a")
        sys.exit(0)
    else:
        os.waitpid(pid, 0)
        for name in workbench.namespaces.namespaces:
            if name == "mount": continue
            ns = getattr(workbench.namespaces, name)
            if not ns.available: continue
            path = "%s/%s" % (ns_bind_dir, ns.entry)
            i = random.randint(0, 1)
            if i == 0:
                print "umount %s by umount" % path
                workbench.umount(path)
            else:
                print "umount %s by umount2" % path
                workbench.umount2(path, "force")
