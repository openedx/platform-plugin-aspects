"""
Aspects plugins for edx-platform.
"""

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("platform-plugin-aspects")
except PackageNotFoundError:
    __version__ = "unknown"

ROOT_DIRECTORY = Path(os.path.dirname(os.path.abspath(__file__)))
