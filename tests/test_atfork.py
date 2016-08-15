#!/usr/bin/env python

import os
import sys
from distutils.log import warn as printf

this_file_absdir = os.path.dirname(os.path.abspath(__file__))
procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
sys.path.append(procszoo_mod_dir)
from procszoo.c_functions import *

if __name__ == "__main__":
    def procinfo(str):
        if "sched_getcpu" not in show_available_c_functions():
            cpu_idx = -1
        else:
            cpu_idx = sched_getcpu()
        pid = os.getpid()
        ppid = os.getppid()
        uid = os.getuid()
        gid = os.getgid()
        euid = os.geteuid()
        egid = os.getegid()
        hostname = gethostname()
        procs = os.listdir("/proc")
        printf("""%s:
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

    def simple_handler1():
        printf(1)

    def simple_handler2():
        printf(2)

    atfork(prepare=simple_handler1,  child=simple_handler1)
    atfork(parent=parent_hdr, child=child_hdr)
    atfork(prepare=simple_handler2)
    unregister_fork_handlers(parent=parent_hdr, strict=True)

    pid = os.fork()
    if pid == -1:
        raise RuntimeError("do fork failed")
    elif pid == 0:
        printf("child")
    elif pid > 0:
        os.waitpid(pid, 0)
        printf("parent")
