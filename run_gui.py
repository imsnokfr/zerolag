#!/usr/bin/env python3
"""
ZeroLag GUI Launcher

Simple launcher script for the ZeroLag graphical user interface.
This script can be used to start the GUI application directly.

Usage:
    python run_gui.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.gui.application import main
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"Error importing ZeroLag GUI: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"Error starting ZeroLag GUI: {e}")
    sys.exit(1)
