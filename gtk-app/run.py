#!/usr/bin/env python3
"""Launcher script for Physica GTK application"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import physica_gtk
sys.path.insert(0, str(Path(__file__).parent))

# In Flatpak, Python modules are in /app/lib/python3.13/site-packages
# Add this to sys.path if it exists
if os.path.exists('/app/lib/python3.13/site-packages'):
    sys.path.insert(0, '/app/lib/python3.13/site-packages')
elif os.path.exists('/app/lib/python3.12/site-packages'):
    sys.path.insert(0, '/app/lib/python3.12/site-packages')

from physica_gtk.main import main

if __name__ == '__main__':
    sys.exit(main())

