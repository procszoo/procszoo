#!/usr/bin/env python

import os
import sys
cwd = os.path.abspath("%s/.." % os.path.dirname(os.path.abspath(__file__)))
sys.path.append("%s" % cwd)
from procszoo.utils import workbench

if __name__ == "__main__":
    def procinfo(str):
        if "sched_getcpu" not in workbench.show_available_c_functions():
            cpu_idx = -1
        else:
            cpu_idx = workbench.sched_getcpu()
        pid = os.getpid()
        ppid = os.getppid()
        uid = os.getuid()
        gid = os.getgid()
        euid = os.geteuid()
        egid = os.getegid()
        hostname = workbench.gethostname()
        procs = os.listdir("/proc")
        print("""%s:
        cpu: %d pid: %d ppid: %d
        uid %d gid %d euid %d egid %d
        hostname: %s
        procs: %s"""
        % (str, cpu_idx, pid, ppid, uid, gid, euid, egid,
               hostname, ", ".join(procs[-4:])))
    def prepare_hdr():
        procinfo("prepare handler")
    def parent_hdr():
        procinfo("parent handler")

    def child_hdr():
        procinfo("child handler")

    workbench.atfork(prepare=prepare_hdr, parent=parent_hdr, child=child_hdr)

    pid = os.fork()

    if pid == -1:
        raise RuntimeError("do fork failed")
    elif pid == 0:
        print "child"
    elif pid > 0:
        os.waitpid(pid, 0)
        print "parent"
