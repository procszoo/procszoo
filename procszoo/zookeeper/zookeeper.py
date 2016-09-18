import sys
import os
import struct
import signal
from pprint import pprint
from .. import c_functions

class Zookeeper(object):
    def __init__(self):
        self.zoos = {}
        pass

