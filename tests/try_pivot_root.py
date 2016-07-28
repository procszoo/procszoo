#!/usr/bin/env python
import os
import sys
import random
from ctypes import c_char_p

cwd = os.path.abspath("%s/.." % os.path.dirname(os.path.abspath(__file__)))
sys.path.append("%s" % cwd)
from procszoo.utils import workbench

if __name__ == "__main__":
    workdir = "/tmp/new-root"
    new_root = "."
    put_old = "old-root" 

    print "we will test pivot_root function"
    if os.path.exists(workdir):
        pass
    else:
        os.mkdir(workdir)

    workbench.mount(source="none", target=workdir, filesystemtype='tmpfs',
                    mount_type="unchanged", data="size=500M")
    os.chdir(workdir)
    possible_path = [
        "/boot/initramfs-%s.img" % os.uname()[2],
        "/boot/initrd.img-%s" % os.uname()[2],]
    for path in possible_path:
        if os.path.exists(path):
            print "%s could be as our rootfs, let's copy it" % path
            break
        else:
            path = None

    if path is None:
        print "cannot create rootfs, quit"
        sys.exit(0)

    os.system("rm -f ./rootfs.gz;cp %s ./rootfs.gz" % path)
    print "copying %s done, let's decompress it" % path
    os.system("gzip -c -d ./rootfs.gz | cpio -idum 2>/dev/null")
    print "let's try pivot_root"
    if not os.path.exists(put_old):
        os.mkdir(put_old)
    workbench.pivot_root(new_root, put_old)
    print "done. then,  we quit"
    sys.exit(0)
