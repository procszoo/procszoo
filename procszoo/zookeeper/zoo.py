from __future__ import absolute_import, unicode_literals, print_function

import logging
import os
import struct
import sys

logging.basicConfig(level=logging.DEBUG)

from procszoo.zookeeper.zoo_init import ZooInit
from procszoo import c_functions
from procszoo.ipc import RPCPeer

LOGGER = logging.getLogger(__name__)


class ZooError(Exception):
    pass


class ZooCreationError(ZooError):
    pass


class Zoo(object):
    def __init__(self, local_rpc_peer=None):
        self.watcher_pid = 0
        self.init_pid = 0
        self._local_rpc_peer = RPCPeer() if local_rpc_peer is None else local_rpc_peer
        self._init_rpc_sock = RPCPeer.new_netlink_socket()
        self._init_rpc_nl_pid = self._init_rpc_sock.getsockname()[0]

        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            self.watcher_proc(w)
            sys.exit(0)
        self.watcher_pid = pid
        os.close(w)
        try:
            self.init_pid = struct.unpack("l", os.read(r, 8))[0]  # wait for init pid
        except Exception as e:
            raise ZooCreationError("Zooinit process exited unexpectedly.")

        LOGGER.debug("watcher_pid=%s, init_pid=%s", self.watcher_pid, self.init_pid)
        os.close(r)

    def state(self):
        return False

    def hello(self, name):
        return self._local_rpc_peer.talk_to(self._init_rpc_nl_pid).hello(name)

    def issue(self, cmd, *args):
        return self._local_rpc_peer.talk_to(self._init_rpc_nl_pid).issue(cmd, *args)
        pass

    def watcher_proc(self, pipe_w):
        c_functions.unshare(['pid'])
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            self.init_proc(w)
            sys.exit(0)
        os.close(w)
        os.read(r, 1)  # wait for init process
        os.close(r)
        os.write(pipe_w, struct.pack("l", pid))  # notify root process with init pid
        os.close(pipe_w)
        self.pid = pid
        os.waitpid(pid, 0)

    def init_proc(self, pipe_w):
        LOGGER.debug("init: unshare " + ", ".join(['cgroup', 'ipc', 'net', 'mount', 'uts']))
        c_functions.unshare(['cgroup', 'ipc', 'mount', 'uts'])
        LOGGER.debug("init: mount /proc")
        os.system("mount --make-private -t none none /proc")
        os.system("mount -t proc proc /proc")

        os.close(pipe_w)  # notify watcher process
        print("init: inited")
        # os.system("sleep 5")
        ZooInit(self._init_rpc_sock.fileno()).serve()

    def wait_all(self):
        os.waitpid(self.watcher_pid, 0)


zoo = Zoo()
os.system("sleep 1")
print("Message from server: %s" % zoo.hello("ProcsIPC"))
print("Message from server: %s" % zoo.issue("/usr/bin/ps", "/usr/bin/ps", "-ef"))
zoo.wait_all()
