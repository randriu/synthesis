"""
api - User-friendly API for PAYNT as a Python library.

This module exposes high-level functions for programmatic use of 
"""

from . import version


def get_version():
    """Return PAYNT version string."""

    return version.__version__


