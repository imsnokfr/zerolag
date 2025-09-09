"""
ZeroLag GUI Package

This package contains the PyQt5-based graphical user interface for ZeroLag.
It provides a modern, dark-themed interface for controlling input optimization
settings and monitoring performance in real-time.

Modules:
    - main_window: Main application window with all controls and monitoring
    - application: Main application class and entry point
"""

from .main_window import ZeroLagMainWindow
from .application import ZeroLagApplication, main

__all__ = ['ZeroLagMainWindow', 'ZeroLagApplication', 'main']