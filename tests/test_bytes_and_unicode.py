#!/usr/bin/env python
import os
import sys

try:
    from procszoo.c_functions import *
except ImportError:
    this_file_absdir = os.path.dirname(os.path.abspath(__file__))
    procszoo_mod_dir = os.path.abspath("%s/.." % this_file_absdir)
    sys.path.append(procszoo_mod_dir)
    from procszoo.c_functions import *
from procszoo.utils import *

if sys.version_info >= (3, 0):
    unicode_str = "Hello"
    bytes_str = b"Hello"
    char = chr(0x006)

    for s in unicode_str, bytes_str, char:
        printf(type(to_unicode(s)))

    for s in unicode_str, bytes_str, char:
        printf(type(to_bytes(s)))
else:
    unicode_str = "Hello".decode('utf-8')
    bytes_str = "Hello"
    char = chr(0x006)

    for s in unicode_str, bytes_str, char:
        printf(type(to_unicode(s)))

    for s in unicode_str, bytes_str, char:
        printf(type(to_bytes(s)))
