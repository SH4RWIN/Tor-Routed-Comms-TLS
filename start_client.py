#!/usr/bin/env python3
"""
Dark Comm Chat Client Launcher
Starts the chat client from the root directory
"""

import sys
import os

# Add the client directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from client import main

if __name__ == "__main__":
    main()
