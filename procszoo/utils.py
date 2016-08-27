import sys
from distutils.log import warn

def printf(text):
    sys.stdout.write('%s\n' % text)

__all__ = ['warn', 'printf']
