#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2019-2025, The OpenROAD Authors

"""
Standalone launcher for the 3D Block Stack Viewer.

This script launches the GUI viewer for .3dbx and .3dbv files.
"""

import sys
from pathlib import Path

# Add the package to the path if running from source
package_dir = Path(__file__).parent
if package_dir not in sys.path:
    sys.path.insert(0, str(package_dir))

try:
    from py3dblox.viewer import main
except ImportError as e:
    print("Error: Could not import the viewer module.")
    print("\nThe viewer requires matplotlib and numpy.")
    print("Please install them with:")
    print("  pip install matplotlib numpy")
    print("\nOr install with viewer support:")
    print("  pip install -e '.[viewer]'")
    print(f"\nDetails: {e}")
    sys.exit(1)

if __name__ == '__main__':
    main()
