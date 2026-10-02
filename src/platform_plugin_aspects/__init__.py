"""
Aspects plugins for edx-platform.
"""

import os
from importlib.metadata import version
from pathlib import Path

__version__ = version("platform-plugin-aspects")

ROOT_DIRECTORY = Path(os.path.dirname(os.path.abspath(__file__)))
