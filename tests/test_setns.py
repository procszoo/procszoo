#!/usr/bin/env python
import os
import sys
import random

try:
    from procszoo.c_functions import *
except ImportError:
    this_file_absdir = os.path.dirname(os.path.abspath(__file__))
    procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
    sys.path.append(procszoo_mod_dir)
    from procszoo.c_functions import *
from procszoo.utils import *

if __name__ == "__main__":
    if "setns" not in show_available_c_functions():
        warn("setns func unavailable, quit")
        sys.exit(1)
    elif not net_namespace_available():
        warn("net namespace unavailable, quit")
        sys.exit(1)
    ns_bind_dir = "/tmp/ns"

    maproot=False
    if user_namespace_available():
        maproot=True

    try:
        spawn_namespaces(ns_bind_dir=ns_bind_dir, func=lambda: None,
                             maproot=maproot)
    except NamespaceRequireSuperuserPrivilege as e:
        warn(e)
        sys.exit(1)
    except Exception as e:
        warn(e)
        sys.exit(1)

    pid = os.fork()
    if pid == -1:
        raise RuntimeError("failed to do a fork")
    if pid == 0:
        try:
            setns(path="/tmp/ns/net", namespace="net")
        except NamespaceRequireSuperuserPrivilege as e:
            warn(e)
            sys.exit(1)
        else:
            os.system("ifconfig -a")
            sys.exit(0)
    else:
        os.waitpid(pid, 0)
        for name, available in show_namespaces_status():
            if name == "mount": continue
            if not available: continue
            ns = get_namespace(name)
            path = "%s/%s" % (ns_bind_dir, ns.entry)
            i = random.randint(0, 1)
            if i == 0:
                printf("umount %s by umount" % path)
                umount(path)
            else:
                printf("umount %s by umount2" % path)
                umount2(path, "force")
