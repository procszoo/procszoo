#!/usr/bin/env python
import os
import sys
from ctypes import c_char_p

try:
    from procszoo.c_functions import *
except ImportError:
    this_file_absdir = os.path.dirname(os.path.abspath(__file__))
    procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
    sys.path.append(procszoo_mod_dir)
    from procszoo.c_functions import *
from procszoo.utils import *


def try_pivot_root():
    workdir = "/tmp/new-root"
    new_root = "."
    put_old = "old-root"

    printf("we will test pivot_root function")
    if os.path.exists(workdir):
        pass
    else:
        os.mkdir(workdir)

    workbench.mount(source="none", target=workdir, filesystemtype='tmpfs',
                    mount_type="unchanged", data="size=500M")
    os.chdir(workdir)
    possible_path = ["/boot/initramfs-%s.img" % os.uname()[2],]
    for path in possible_path:
        if os.path.exists(path):
            printf("%s could be as our rootfs, let's copy it" % path)
            break
        else:
            path = None

    if path is None:
        printf("cannot create rootfs, quit")
        sys.exit(0)

    os.system("rm -f ./rootfs.gz;cp %s ./rootfs.gz" % path)
    printf("copying %s done, let's decompress it" % path)
    cmd = "cpio -i -d -H newc --no-absolute-filenames 2>/dev/null"
    os.system("gzip -c -d ./rootfs.gz | %s" % cmd)
    printf("let's try pivot_root")
    if not os.path.exists(put_old):
        os.mkdir(put_old)
    workbench.pivot_root(new_root, put_old)
    printf("done. then,  we quit")

if __name__ == "__main__":
    euid = os.geteuid()
    if euid != 0:
        warn("need superuser privilege, quit")
        sys.exit(1)

    maproot=False
    if user_namespace_available():
        maproot=True

    try:
        spawn_namespaces(maproot=maproot, func=try_pivot_root)
    except NamespaceRequireSuperuserPrivilege as e:
        warn(e)
        sys.exit(1)
