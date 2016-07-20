# Copyright 2016 Red Hat, Inc. All Rights Reserved.
# Licensed to GPL under a Contributor Agreement.

"""Export libc functions that operate Linux namespaces."""

import os
import sys
import atexit
import re
import struct
from ctypes import (cdll, c_int, c_long, c_char_p, c_size_t, string_at,
                    create_string_buffer, c_void_p, CFUNCTYPE, pythonapi)
from copy import copy
import pickle

"""The following manpages will be help to understand Linux namespaces
and C functions that this module exports

    namespaces(7)
    pthread_atfork(3)
    unhsare(2)
    setns(2)
    pivot_root(2)
    sched_getcpu(3)

Functions:
     atfork(prepare=hdr1, parent=hdr2, child=hdr2)
     unshare(namespaces=None)
     setns(path=path_to_namespace, namespace=namespace)
     mount(source=None, target=None, mount_type=None,
           filesystemtype=None, data=None)
     umount(mountpoint)
     umount2(mountpoint, behavior)
     spawn_namespaces(namespaces=None, maproot=True, mountproc=True,
                      mountpoint="/proc", ns_bind_dir=None, nscmd=None,
                      propagation=None, negative_namespaces=None)
     pivot_root(old_root, new_root)
     sched_getcpu()
     fork()
     gethostname()
     sethostname(hostname=None)
     is_namespace_available(namespace)
         namespaces could be one of:
          "ipc", "net", "mount", "pid", "user", "uts"

Misc variables:
     __version__
"""
if os.uname()[0] != "Linux":
    raise ImportError("only support Linux platform")

__version__ = '0.90'
__all__ = [
    "unshare", "setns", "sched_getcpu", "fork", "atfork", "mount", "umount",
    "umount2", "gethostname", "sethostname", "pivot_root", "spawn_namespaces",
    "is_namespace_available", "workbench"]

class Toolbox(object):
    """
    The class is instanced as a singleton. While we will export the
    instance, but unless know exactly what you are doing, don't use
    this instance directly.
    """

    HOST_NAME_MAX = 256
    ForkHandlers = []
    CFunctions = {}
    Namespaces = {}
    CDLL = cdll.LoadLibrary(None)
    ACLCHAR = 0x006

    def __init__(self):
        self.init_c_functions()
        self.init_namespaces()

    class CFunction(object):
        """
        Python class for c library function. These functions could be accessed
        by workbench.c_func_name, e.g., c_func_unshare.
        """
        def __init__(self, exported_name=None, argtypes=None,
                     restype=c_int, default_args=None,
                     failed=lambda res: res != 0,
                     possible_c_func_names=None, func=None):
            self.exported_name = exported_name
            self.failed = failed
            self.default_args = default_args
            self.func = func
            self.possible_c_func_names = possible_c_func_names
            if self.possible_c_func_names is None:
                self.possible_c_func_names = [exported_name]

            for name in self.possible_c_func_names:
                if hasattr(Toolbox.CDLL, name):
                    func = getattr(Toolbox.CDLL, name)
                    func.argtypes = argtypes
                    func.restype = restype
                    self.func = func
                    break

    class Namespace(object):
        """
        Wrapper of namespace. You can check whether a namespace is available or
        not by workbench.is_namespace_name_available. E.g.,
        workbench.is_user_namespace_available. For namespaces name, pls
        reference namespaces(7). In the module, namespaces names are all
        lower-cases: user, net, mount, ipc, pid, uts.
        """
        def __init__(self, name, available=None, capabilities=None,
                         macro=None, value=0, entry=None):
            self.name = name
            self.available = available
            self.capabilities=['CAP_SYS_ADMIN']
            if capabilities is not None:
                self.capabilities = capabilities
            self.macro = macro
            self.value = value
            self.entry = name.lower()
            if entry:
                self.entry = entry
            self.init_available_status()

        def init_available_status(self):
            if self.available in [True, False]:
                return

            pid = os.getpid()
            path = "/proc/%d/ns/%s" % (pid, self.entry)
            if os.path.exists(path):
                self.available = True
            else:
                self.available = False
            return

            kernel_config = "/boot/config-%s" % os.uname()[2]
            if os.path.exists(kernel_config):
                regex = re.compile('^CONFIG_%s_NS=(y|m)$' % self.entry.upper())
                hdr = open(kernel_config, 'r')
                for line in hdr:
                    if regex.match(line):
                        self.available = True
                        return
                hdr.close()
            self.available = False


    @classmethod
    def _is_64bit(cls):
        return struct.calcsize('P') * 8 == 64

    def init_c_functions(self):
        exported_name = "unshare"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_int])

        exported_name = "sched_getcpu"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=None,
            failed=lambda res: res == -1)

        exported_name = "setns"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_int, c_int],
            default_args={
                "file_instance": None,
                "file_descriptor": None,
                "path": None,
                "namespace_type": 0,})

        exported_name = "syscall"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            possible_c_func_names=["syscall"])

        exported_name = "mount"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_char_p, c_char_p, c_char_p, c_long, c_void_p],
            default_args={
                "source": None,
                "target": None,
                "filesystemtype": None,
                "flags": None,
                "data": None,})
        func = self.CFunctions[exported_name]
        func.flags = {
            "MS_NOSUID": 2, "MS_NODEV": 4,
            "MS_NOEXEC": 8, "MS_REC": 16384,
            "MS_PRIVATE": 1 << 18,
            "MS_SLAVE": 1 << 19,
            "MS_SHARED": 1 << 20,
            "MS_BIND": 4096,
        }
        func.propagation = {
            "slave": ["MS_REC", "MS_SLAVE"],
            "private": ["MS_REC", "MS_PRIVATE"],
            "shared": ["MS_REC", "MS_SHARED"],
            "bind": ["MS_BIND"],
            "mount_proc": ["MS_NOSUID", "MS_NODEV", "MS_NOEXEC"],
            "unchanged": [],
        }

        exported_name = "umount"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_char_p])

        exported_name = "umount2"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_char_p, c_int])
        func = self.CFunctions[exported_name]
        func.flags = {
            "MNT_FORCE": 1,
            "MNT_DETACH": 2,
            "MNT_EXPIRE": 4,
            "UMOUNT_NOFOLLOW": 8,
        }
        func.behaviors = {
            "force": "MNT_FORCE",
            "detach": "MNT_DETACH",
            "expire": "MNT_EXPIRE",
            "nofollow": "UMOUNT_NOFOLLOW",
        }

        self.fork_handler_prototype = CFUNCTYPE(None)
        self.null_handler_pointer = self.fork_handler_prototype()
        self.register_fork_handler(self.null_handler_pointer)
        hdr_prototype = self.fork_handler_prototype
        exported_name = "pthread_atfork"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            possible_c_func_names=[exported_name, "__register_atfork"],
            argtypes=[hdr_prototype, hdr_prototype, hdr_prototype],
            failed=lambda res: res == -1,
            default_args={
                "prepare": self.null_handler_pointer,
                "parent": self.null_handler_pointer,
                "child": self.null_handler_pointer,})

        exported_name = "gethostname"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_char_p, c_size_t])

        exported_name = "sethostname"
        self.CFunctions[exported_name] = self.CFunction(
            exported_name=exported_name,
            argtypes=[c_char_p, c_size_t])

    def init_namespaces(self):
        self.Namespaces["cgroup"] = self.Namespace(
            name="cgroup", macro='CLONE_CGROUP',
            value=0x02000000, entry='cgroup')

        self.Namespaces["ipc"] = self.Namespace(
            name="ipc", macro='CLONE_NEWIPC', value=0x08000000, entry='ipc')

        self.Namespaces["net"] = self.Namespace(
            name="net", macro='CLONE_NEWNET',
            value=0x40000000, entry="net")

        self.Namespaces["mount"] = self.Namespace(
            name="mount", entry="mnt", macro='CLONE_NEWNS',
            value=0x00020000, available=True)

        self.Namespaces["pid"] = self.Namespace(
            name="pid", macro='CLONE_NEWPID', value=0x20000000, entry='pid')

        self.Namespaces["user"] = self.Namespace(
            name="user", macro='CLONE_NEWUSER', value=0x10000000, entry='user')
        self.Namespaces["user"].group_control_keys = ["allow", "deny"]

        self.Namespaces["uts"] = self.Namespace(
            name="uts", macro='CLONE_NEWUTS', value=0x04000000, entry='uts')            

    def register_fork_handler(self, hdr):
        if hdr not in self.ForkHandlers:
            self.ForkHandlers.append(hdr)

    def pthread_atfork(self, prepare=None, parent=None, child=None):
        """
        This function will let us to insert our codes before and after fork
            prepare()
            pid = os.fork()
            if pid == 0:
                child()
                ...
            elif pid > 0:
                parent()
                ...
        """
        func_obj = self.CFunctions["pthread_atfork"]

        hdr_prototype = self.fork_handler_prototype
        if prepare is None:
            prepare = self.null_handler_pointer
        else:
            prepare = hdr_prototype(prepare)
        if parent is None:
            parent = self.null_handler_pointer
        else:
            parent = hdr_prototype(parent)
        if child is None:
            child = self.null_handler_pointer
        else:
            child = hdr_prototype(child)

        for hdr in prepare, parent, child:
            self.register_self.fork_handler(hdr)

        return self.c_func_pthread_atself.fork(prepare, parent, child)

    def _check_namespaces_available_status(self):
        """
        On rhel6/7, the kernel default does not enable all namespaces
        that it supports.
        """
        EINVAL = 22
        r, w = os.pipe()

        pid0 = self.fork()
        if pid0 == 0:
            pid1 = self.fork()
            if pid1 == 0:
                os.close(r)
                tmpfile = os.fdopen(w, 'wb')
                keys = []
                unshare = self.CFunctions["unshare"].func
                for key, ns_obj in self.Namespaces.iteritems():
                    val = ns_obj.value
                    res = unshare(c_int(val))
                    _errno_c_int = c_int.in_dll(pythonapi, "errno")
                    if res == -1:
                        if _errno_c_int.value != EINVAL:
                            keys.append(key)
                    else:
                        keys.append(key)

                pickle.dump(keys, tmpfile)
                sys.exit(0)
            else:
                os.waitpid(pid1, 0)
                sys.exit(0)
        else:
            os.close(w)
            tmpfile = os.fdopen(r, 'rb')
            os.waitpid(pid0, 0)
            keys = pickle.load(tmpfile)
            tmpfile.close

            for key in self.Namespaces.keys():
                if not key in keys:
                    ns_obj = self.Namespaces[key]
                    ns_obj.available = False

    def __getattr__(self, name):
        if name.startswith("c_func_") and name.endswith("_available"):
            name = name.replace("c_func_", "")
            name = name.replace("_available", "")

            if (self.CFunctions.has_key(name)
                and self.CFunctions[name].func is not None):
                return True
            else:
                return False

        elif name.startswith("is_") and name.endswith("_namespace_available"):
            name = name.replace("is_", "")
            name = name.replace("_namespace_available", "")

            if self.Namespaces.has_key(name):
                ns_obj = self.Namespaces[name]
                return ns_obj.available
            else:
                return False

        elif name.startswith("c_func_"):
            c_func_name = name
            name = name.replace("c_func_", "")
            if self.CFunctions.has_key(name):
                func_obj = self.CFunctions[name]
                c_func = func_obj.func
                context = locals()
                def c_func_wrapper(*args, **context):
                    res = c_func(*args)
                    c_int_errno = c_int.in_dll(pythonapi, "errno")
                    if func_obj.failed(res):
                        raise RuntimeError(os.strerror(c_int_errno.value))
                    return res

                return c_func_wrapper
            else:
                raise Runtime("C function '%s' not found" % name)

    def mount(self, source=None, target=None, mount_type=None,
              filesystemtype=None, data=None):
        if not [arg for arg in [source, target, filesystemtype, mount_type]
                if arg is not None]:
            return
        func_obj = self.CFunctions["mount"]

        if source is None:
            source=c_char_p()
        if target is None:
            target=c_char_p()
        if filesystemtype is None:
            filesystemtype = c_char_p()
        if mount_type is None:
            mount_type = "unchanged"
        if data is None:
            data=c_void_p()

        mount_flags = func_obj.propagation[mount_type]
        mount_vals = [func_obj.flags[k] for k in mount_flags]
        flags = reduce(lambda res, val: res | val, mount_vals, 0)
        self.c_func_mount(source, target, filesystemtype, flags, data)

    def mount_proc(self, mountpoint="/proc"):
        self.mount(source="none", target=mountpoint, mount_type="private")
        self.mount(source="proc", target=mountpoint, filesystemtype="proc",
                   mount_type="mount_proc")

    def umount(self, mountpoint=None):
        if mountpoint is None:
            return
        if not isinstance(mountpoint, basestring):
            raise RuntimeError("mountpoint should be a path to a mount point")
        if not os.path.exists(mountpoint):
            raise RuntimeError("mount point '%s': cannot found")
        self.c_func_umount(mountpoint)

    def umount2(self, mountpoint=None, behavior=None):
        func_obj = self.CFunctions["umount2"]
        if mountpoint is None:
            return
        if not isinstance(mountpoint, basestring):
            raise RuntimeError("mountpoint should be a path to a mount point")
        if not os.path.exists(mountpoint):
            raise RuntimeError("mount point '%s': cannot found")

        if behavior is None or behavior not in func_obj.behaviors.keys():
            raise RuntimeError("behavior should be one of [%s]"
                               % ", ".join(func_obj.behaviors.keys()))

        flag = func_obj.flags[func_obj.behaviors[behavior]]
        self.c_func_umount2(mountpoint, c_int(flag))

    def set_propagation(self, type=None):
        if type is None:
            return
        mount_func_obj = self.CFunctions["mount"]
        if type not in mount_func_obj.propagation.keys:
            raise RuntimeError("%s: unknown propagation type" % type)
        if type == "unchanged":
            return
        self.mount(source="none", target="/", mount_type=type)

    def unshare(self, namespaces=None):
        if namespaces is None:
            return

        target_flags = []
        for k in namespaces:
            ns = self.Namespaces[k]
            if ns.available:
                target_flags.append(ns.value)

        flags = reduce(lambda res, flag: res | flag, target_flags, 0)
        self.c_func_unshare(flags)

    def setns(self, **kwargs):
        """
        workbench.setns(namespace, namespace_type)

        E.g., setns(pid=1234, "pid")
        """
        keys = ["fd", "path", "pid", "file_obj"]
        wrong_keys = [k for k in keys if k in kwargs.keys()]
        if len(wrong_keys) != 1:
            raise TypeError("complicating named argument found: %s"
                            % ", ".join(wrong_keys))

        _kwargs = copy(kwargs)
        namespace = 0
        if  kwargs.has_key("namespace"):
            ns = kwargs["namespace"]
            if isinstance(ns, str) and self.Namespaces.has_key(ns):
                namespace = self.Namespaces[ns].value
            else:
                if namespace_wrong:
                    raise TypeError("unkonwn namespace found")
        _kwargs["namespace"] = namespace

        if kwargs.has_key("fd"):
            fd = kwargs["fd"]
            if not (isinstance(fd, int) or isinstance(fd, long)):
                raise TypeError("unavailable file descriptor found")
        elif kwargs.has_key("path"):
            path = os.path.abspath(kwargs["path"])
            entry = os.path.basename(path)
            if kwargs.has_key("namespace"):
                ns = kwargs["namespace"]
                ns_obj = self.Namespaces[ns]
                ns_obj_entry = ns_obj.entry
                if entry != ns_obj_entry:
                    raise TypeError("complicating path and namespace args found")
            if not os.path.exists(path):
                raise TypeError("%s not existed" % path)

            file_obj = open(path, 'r')
            _kwargs["file_obj"] = file_obj
            _kwargs["fd"] = file_obj.fileno()
            _kwargs["path"] = path
        elif kwargs.has_key("pid"):
            pid = kwargs["pid"]
            if namespace == 0:
                raise TypeError("pid named arg need a namespace")
            if not (isinstance(pid, int) or isinstance(pid, long)):
                raise TypeError("unknown pid found")
            ns = kwargs["namespace"]
            ns_obj = self.Namespaces[ns]
            entry = ns_obj.entry
            path = "/proc/%d/ns/%s" % (pid, entry)
            if os.path.exists(path):
                file_obj = open(path, 'r')
                _kwargs["file_obj"] = file_obj
                _kwargs["fd"] = file_obj.fileno()
        elif kwargs.has_key("file_obj"):
            file_obj = kwargs["file_obj"]
            _kwargs["fd"] = file_obj.fileno()

        flags = c_int(_kwargs["namespace"])
        fd = c_int(_kwargs["fd"])
        if self.c_func_setns_available:
            return self.c_func_setns(fd, flags)
        else:
            if self._is_64bit():
                NR_SETNS = 308
            else:
                NR_SETNS = 346
            return self.c_func_syscall(c_long(NR_SETNS), fd, flags)

    @classmethod
    def fork(cls):
        pid = os.fork()
        _errno_c_int = c_int.in_dll(pythonapi, "errno")
        if pid == - 1:
            raise RuntimeError(os.strerror(_errno_c_int.value))
        return pid

    def gethostname(self):
        buf_len = 256
        buf = create_string_buffer(buf_len)
        self.c_func_gethostname(buf, c_size_t(buf_len))
        return string_at(buf)

    def sethostname(self, hostname=None):
        if hostname is None:
            return
        buf_len = c_size_t(len(hostname))
        buf = create_string_buffer(hostname)
        return self.c_func_sethostname(buf, buf_len)

    def pivot_root(self, old_root, new_root):
        if not isinstance(old_root, basestring):
            raise RuntimeError("old_root argument is not an available path")
        if not isinstance(new_root, basestring):
            raise RuntimeError("new_root argument is not an available path")
        if not os.path.exists(old_root):
            raise RuntimeError("%s: no such directory" % old_root)
        if not os.path.exists(new_root):
            raise RuntimeError("%s: no such directory" % new_root)

        if self._is_64bit():
            NR_PIVOT_ROOT = 155
        else:
            NR_PIVOT_ROOT = 217
        return self.c_func_syscall(c_long(NR_PIVOT_ROOT), old_root, new_root)

    def adjust_namespaces(self, namespaces=None, negative_namespaces=None):
        self._check_namespaces_available_status()
        available_namespaces = []
        for k in self.Namespaces.keys():
            ns = self.Namespaces[k]
            if ns.available:
                available_namespaces.append(k)

        if namespaces is None:
            namespaces = available_namespaces

        unavailable_namespaces = [ns for ns in namespaces
                                  if ns not in self.Namespaces.keys()]
        if unavailable_namespaces:
            raise UnknownNamespaceFound(namespaces=unavailable_namespaces)

        if negative_namespaces:
            for ns in negative_namespaces:
                if ns in namespaces: namespaces.remove(ns)

        return namespaces

    @classmethod
    def write2file(cls, path, str=None):
        if path is None:
            raise RuntimeError("path cannot be none")
        if str is None:
            str = ""
        if os.path.exists(path):
            hdr = open(path, 'w')
        else:
            hdr = open(path, 'a')

        hdr.write(str)
        hdr.close()

    def setgroups_control(self, str="deny"):
        ctrl_keys = self.Namespaces["user"].group_control_keys
        if str not in ctrl_keys:
            raise RuntimeError("group control should be %s"
                               % ", ".join(ctrl_keys))
        path = "/proc/self/setgroups"
        if os.path.exists(path):
            self.write2file(path, str)

    def map_id(self, map_file, map):
        path = "/proc/self/%s" % map_file
        if os.path.exists(path):
            self.write2file(path, map)
        else:
            raise RuntimeError("%s: No such file" % path)

    def bind_ns_files(self, pid, namespaces=None, ns_bind_dir=None):
        if ns_bind_dir is None or namespaces is None:
            return

        if not os.path.exists(ns_bind_dir):
            os.mkdir(ns_bind_dir)

        if not os.access(ns_bind_dir, os.R_OK | os.W_OK):
            raise RuntimeError("cannot access %s" % bind_ns_dir)

        path="/proc/%d/ns" % pid
        for ns in namespaces:
            if ns == "mount": continue
            ns_obj = self.Namespaces[ns]
            entry = ns_obj.entry
            source = "%s/%s" % (path, entry)
            target="%s/%s" % (ns_bind_dir.rstrip("/"), entry)
            if not os.path.exists(target):
                os.close(os.open(target, os.O_CREAT | os.O_RDWR))
            self.mount(source=source, target=target, mount_type="bind")

    @classmethod
    def find_my_init(cls, paths=None, name=None):
        if paths is None:
            cwd = os.path.dirname(os.path.abspath(__file__))
            absdir = os.path.abspath("%s/.." % cwd)
            path = os.path.abspath("%s/../libexec" % cwd)
            paths = ["%s/libexec" % absdir,
                     "%s/bin" % absdir,
                     "/usr/local/libexec",
                     "/usr/libexec"]

        if name is None:
            name = "my_init"

        for path in paths:
            my_init = "%s/%s" % (path, name)
            if os.path.exists(my_init):
                return my_init

    @classmethod
    def find_shell(cls, name="bash", shell=None):
        if shell is not None:
            return shell
        if os.environ.has_key("SHELL"):
            return os.environ.get("SHELL")
        for path in ["/bin", "/usr/bin", "/usr/loca/bin"]:
            fpath = "%s/%s" % (path, name)
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                return fpath
        return "sh"

    def _run_cmd_in_new_namespaces(self, r1, w1, r2, w2, namespaces, maproot,
                                   mountproc, mountpoint, nscmd, propagation):
        if maproot:
            uid = os.geteuid()
            gid = os.getegid()

        os.close(r1)
        os.close(w2)

        self.unshare(namespaces)

        r3, w3 = os.pipe()
        r4, w4 = os.pipe()
        pid = self.fork()

        if pid == 0:
            os.close(w1)
            os.close(r2)

            os.close(r3)
            os.close(w4)

            if maproot:
                self.setgroups_control()
                self.map_id("uid_map", "0 %d 1" % uid)
                self.map_id("gid_map", "0 %d 1" % gid)
            if "mount" in namespaces and propagation is not None:
                self.set_propagation(propagation)
            if mountproc:
                self.mount_proc(mountpoint=mountpoint)

            os.write(w3, chr(self.ACLCHAR))
            os.close(w3)

            if ord(os.read(r4, 1)) != self.ACLCHAR:
                raise "sync failed"
            os.close(r4)
            my_init = self.find_my_init()
            if nscmd is None:
                nscmd = self.find_shell()
            args = ["-c", my_init, "--skip-startup-files",
                    "--skip-runit", "--quiet"]
            args.append(nscmd)
            os.execlp("python", *args)
            sys.exit(0)
        else:
            os.close(w3)
            os.close(r4)

            if ord(os.read(r3, 1)) != self.ACLCHAR:
                raise "sync failed"
            os.close(r3)

            os.write(w1, "%d" % pid)
            os.close(w1)

            if ord(os.read(r2, 1)) != self.ACLCHAR:
                raise "sync failed"
            os.close(r2)

            os.write(w4, chr(self.ACLCHAR))
            os.close(w4)

            os.waitpid(pid, 0)
            sys.exit(0)

    def _continue_original_flow(self, r1, w1, r2, w2, namespaces, ns_bind_dir):
       os.close(w1)
       os.close(r2)

       child_pid = os.read(r1, 64)
       os.close(r1)
       try:
           child_pid = int(child_pid)
       except ValueError:
           raise RuntimeError("failed to get the child pid")

       if ns_bind_dir is not None and "mount" in namespaces:
           self.bind_ns_files(child_pid, namespaces, ns_bind_dir)
       os.write(w2, chr(self.ACLCHAR))
       os.close(w2)

    def spawn_namespaces(self, namespaces=None, maproot=True, mountproc=True,
                         mountpoint="/proc", ns_bind_dir=None, nscmd=None,
                         propagation=None, negative_namespaces=None):
        """
        workbench.spawn_namespace(namespaces=["pid", "net", "mount"])
        """
        namespaces = self.adjust_namespaces(namespaces, negative_namespaces)

        if "pid" in namespaces and not is_namespace_available("pid"):
            raise RuntimeError("unsupported OS found")
        if "pid" not in namespaces:
            mountproc = False

        if mountproc:
            mountproc = self.is_mount_namespace_available

        if "pid" in namespaces and mountproc is False:
            raise RuntimeError("new pid namespaces requires remount procfs")

        if maproot and self.is_user_namespace_available:
            if "user" not in namespaces:
                raise UnavailableNamespaceFound(["user"])
        else:
            maproot = False

        r1, w1 = os.pipe()
        r2, w2 = os.pipe()
        pid = self.fork()

        if pid == 0:
            self._run_cmd_in_new_namespaces(
                r1, w1, r2, w2, namespaces, maproot, mountproc, mountpoint,
                nscmd, propagation)
        else:
            self._continue_original_flow(r1, w1, r2, w2, namespaces,
                                         ns_bind_dir)
            def ensure_wait_child_process(pid=pid):
                try:
                    os.waitpid(pid, 0)
                except OSError:
                    pass
            atexit.register(ensure_wait_child_process)

class NamespaceGenericException(Exception):
    #status is copy from mock/py/mockbuild/exception.py
    def __init__(self, namespaces=None, status=80):
        Exception.__init__(self)
        if namespaces:
            self.msg = "NamespaceGenericException: " % ", ".join(namespaces)
        else:
            self.msg = "NamespacesGenericException"
        self.resultcode = status

    def __str__(self):
        return self.msg

class UnknownNamespaceFound(NamespaceGenericException):
    def __init__(self, namespaces=None):
        if namespaces:
            self.msg = "unknown namespaces: %s found" % ", ".join(namespaces)
        else:
            self.msg = "unknown namespaces found"

    def __str__(self):
        return self.msg

class UnavailableNamespaceFound(NamespaceGenericException):
    def __init__(self, namespaces=None):
        if namespaces:
            self.msg = "unavailable namespaces: %s found" % ", ".join(namespaces)
        else:
            self.msg = "unavailable namespaces found"

    def __str__(self):
        return self.msg

def mount(**kwargs):
    """
    mount(source=None, target=None, mount_type=None,
          filesystemtype=None, data=None):

    mount_type is one of "slave", "private", "bind", "mount_proc", "unchanged".
    """
    return workbench.mount(**kwargs)

def umount(mountpoint):
    """
    umount(mountpoint)
    """
    return workbench.umount(mountpoint)

def umount2(mountpoint, behavior):
    """
    umount2(mountpoint, behavior)
    """
    return workbench.umount2(mountpoint, behavior)

def pivot_root(old_root, new_root):
    """
    pivot_root(old_root, new_root)
    """
    return workbench.pivot_root(old_root, new_root)

def spawn_namespaces(**kwargs):
    """
    spawn_namespace(namespaces=None, maproot=True, mountproc=True,
                    mountpoint="/proc", ns_bind_dir=None, nscmd=None,
                    propagation=None, negative_namespaces=None)

    nscmd: program that will run in the new namespace, default is bash or sh.
    """
    return workbench.spawn_namespaces(**kwargs)

def unshare(**kwargs):
    """
    unshare(namespaces=None)
    """
    return workbench.unshare(**kwargs)

def setns(**kwargs):
    """
    setns(pid=pid, namespace=namespace)
    setns(path=path, namespace=namespace)
    """
    return workbench.setns(**kwargs)

def atfork(**kwargs):
    """
    atfork(prepare=prepare, parent=parent, child=child)

    This function will let us to insert our codes before and after fork
        prepare()
        pid = os.fork()
        if pid == 0:
            child()
            ...
        elif pid > 0:
            parent()
            ...
        ...
    """
    return workbench.pthread_atfork(**kwargs)

def sched_getcpu():
    """
    sched_getcpu()
    which cpu the thread is running. See sched_getcpu(3)
    """
    return workbench.c_func_sched_getcpu()

def is_namespace_available(namespace):
    return workbench.__getattr__("is_%s_namespace_available" % namespace)

def fork():
    return workbench.fork()

def gethostname():
    return workbench.gethostname()

def sethostname(hostname=None):
    return workbench.sethostname(hostname)

workbench = Toolbox()
del Toolbox

if __name__ == "__main__":
    spawn_namespaces()
