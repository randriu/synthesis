import sys

if sys.version_info[0] == 2:
    raise ImportError('Python 2.x is not supported for stormpy.')

from .synthesis import *

__version__ = "unknown"
try:
    from ._version import __version__
except ImportError:
    # We're running in a tree that doesn't have a _version.py, so we don't know what our version is.
    pass
