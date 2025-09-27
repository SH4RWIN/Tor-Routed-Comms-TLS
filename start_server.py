#!/usr/bin/env python3
"""
Dark Comm Chat Server Launcher
Starts the chat server from the root directory
"""

import sys
import os

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server import main

if __name__ == "__main__":
    main()
