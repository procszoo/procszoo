#!/usr/bin/env python
import socket
import subprocess
import sys
import os
import logging

from procszoo.ipc import RPCPeer

LOGGER = logging.getLogger(__name__)

class ZooInitAPI(object):
    def __init__(self, zoo_init):
        self.zoo_init = zoo_init

    def hello(self, name):
        s = "Hello, %s!" % name
        print(s)
        return s

    def issue(self, cmd, *args):
        print("run %s %s " % (cmd, args))
        pid = os.fork()
        if pid == 0:
            os.execl(cmd, *args)
        _, status = os.waitpid(pid, 0)
        return status

class ZooInit(object):
    def __init__(self, nl_sock_fd):
        print("netlink socker FD=%s", nl_sock_fd)
        self.zoo_rpc_peer = RPCPeer(
            socket.fromfd(nl_sock_fd, socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_USERSOCK))
        self.zoo_rpc_peer.register_functions_in_object(ZooInitAPI(self))

    def serve(self):

        self.zoo_rpc_peer.run_server_forever()


if __name__ == '__main__':
    nl_sock_fd = int(sys.argv[1])
    ZooInit(nl_sock_fd)
