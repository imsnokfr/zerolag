#!/usr/bin/env python3
"""
ZeroLag Launch Script

This script provides a unified entry point for ZeroLag with options to:
- Launch the main application
- Start monitoring dashboard
- Run performance analysis
- Execute beta testing
- Create releases
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def main():
    """Main launch function."""
    parser = argparse.ArgumentParser(description="ZeroLag Launch Script")
    parser.add_argument("--mode", choices=["gui", "monitor", "analyze", "test", "release"], 
                       default="gui", help="Launch mode")
    parser.add_argument("--platform", choices=["windows", "macos", "linux"], 
                       help="Target platform for release")
    parser.add_argument("--version", default="1.0.0", help="Version for release")
    parser.add_argument("--no-gui", action="store_true", help="Run without GUI")
    
    args = parser.parse_args()
    
    print(f"ZeroLag Launch Script - Mode: {args.mode}")
    print("=" * 50)
    
    if args.mode == "gui":
        launch_gui()
    elif args.mode == "monitor":
        launch_monitoring()
    elif args.mode == "analyze":
        run_analysis()
    elif args.mode == "test":
        run_testing()
    elif args.mode == "release":
        create_release(args.platform, args.version)

def launch_gui():
    """Launch the main ZeroLag GUI."""
    print("Launching ZeroLag GUI...")
    try:
        subprocess.run([sys.executable, "run_gui.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch GUI: {e}")
        sys.exit(1)

def launch_monitoring():
    """Launch the monitoring dashboard."""
    print("Launching monitoring dashboard...")
    try:
        subprocess.run([sys.executable, "monitoring_dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch monitoring: {e}")
        sys.exit(1)

def run_analysis():
    """Run performance analysis."""
    print("Running performance analysis...")
    try:
        subprocess.run([sys.executable, "run_final_tasks.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run analysis: {e}")
        sys.exit(1)

def run_testing():
    """Run beta testing suite."""
    print("Running beta testing suite...")
    try:
        subprocess.run([sys.executable, "tests/beta_testing.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run testing: {e}")
        sys.exit(1)

def create_release(platform, version):
    """Create a release."""
    print(f"Creating release for {platform} version {version}...")
    try:
        subprocess.run([sys.executable, "create_release.py", "--platform", platform, "--version", version], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create release: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
