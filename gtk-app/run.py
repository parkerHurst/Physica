#!/usr/bin/env python3
"""Launcher script for Physica GTK application"""

import sys
from pathlib import Path

# Add parent directory to path so we can import physica_gtk
sys.path.insert(0, str(Path(__file__).parent))

from physica_gtk.main import main

if __name__ == '__main__':
    sys.exit(main())

