#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf

procszoo_mod_dir = os.path.abspath("..")
sys.path.append(procszoo_mod_dir)
from procszoo.utils import *

if sys.version_info > (3, 0):
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
