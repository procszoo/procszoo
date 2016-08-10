#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf

procszoo_mod_dir = os.path.abspath("%s/../.." % os.path.dirname(__file__))
sys.path.append(procszoo_mod_dir)
from procszoo.utils import workbench

if __name__ == "__main__":
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
    sys.exit(0)
