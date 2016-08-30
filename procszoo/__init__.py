import os
from .version import PROCSZOO_VERSION

__version__ = PROCSZOO_VERSION
package_abspath = os.path.dirname(os.path.abspath(__file__))
package_realpath = os.path.dirname(os.path.realpath(__file__))

from .c_functions import *
