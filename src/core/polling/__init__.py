"""
ZeroLag Polling Rate Management Package

This package provides high-frequency polling rate management for gaming peripherals.
It supports polling rates up to 8000Hz with adaptive performance optimization.

Modules:
    - polling_manager: Main polling rate manager with adaptive optimization
"""

from .polling_manager import (
    PollingManager, PollingConfig, PollingStats, 
    PollingRate, PollingMode
)

__all__ = [
    'PollingManager', 'PollingConfig', 'PollingStats',
    'PollingRate', 'PollingMode'
]
