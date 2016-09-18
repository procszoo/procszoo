import os
import sys

class ZookeeperDaemon(object):
    def __init__(self):
        self.deamon_pid = 0
        pass

    def run(self):
        self.deamon_pid = os.fork()
        if self.deamon_pid > 0:
            return
        os.umask(0)
        os.setsid()
        os.chdir("/")
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
        pass

zookeeperd = ZookeeperDaemon()
zookeeperd.run()
