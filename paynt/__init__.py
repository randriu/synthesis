__version__: str = "unknown"

try:
    from ._version import __version__
except ImportError:
    # We're running in a tree that doesn't have a _version.py, so we don't know what our version is.
    pass


def version() -> str:
    return __version__


# Expose API functions at package level -- placed after the version-detection bootstrap above on purpose
from .api import *  # noqa: E402

from . import dt  # noqa: E402
