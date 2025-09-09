#!/usr/bin/env python3
"""
ZeroLag Main Application Entry Point

This is the main entry point for the ZeroLag gaming input optimization application.
Supports both GUI and command-line modes.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="ZeroLag - Gaming Input Optimization")
    parser.add_argument("--gui", action="store_true", help="Start GUI mode (default)")
    parser.add_argument("--cli", action="store_true", help="Start command-line mode")
    parser.add_argument("--test", action="store_true", help="Run input handler test")
    parser.add_argument("--version", action="version", version="ZeroLag 1.0.0")
    
    args = parser.parse_args()
    
    # Default to GUI mode if no mode specified
    if not args.cli and not args.test:
        args.gui = True
    
    if args.gui:
        # Start GUI mode
        try:
            from src.gui.application import main as gui_main
            return gui_main()
        except ImportError as e:
            print(f"Error starting GUI mode: {e}")
            print("Please ensure PyQt5 is installed: pip install PyQt5")
            return 1
        except Exception as e:
            print(f"GUI error: {e}")
            return 1
            
    elif args.test:
        # Run input handler test
        try:
            from test_zerolag import main as test_main
            return test_main()
        except ImportError as e:
            print(f"Error running test: {e}")
            return 1
        except Exception as e:
            print(f"Test error: {e}")
            return 1
            
    else:
        # CLI mode
        print("ZeroLag - Gaming Input Optimization")
        print("Version: 1.0.0")
        print("CLI mode not yet implemented.")
        print("Use --gui for graphical interface or --test to run input handler test.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
