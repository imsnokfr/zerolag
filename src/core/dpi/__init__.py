"""
ZeroLag DPI Emulation Package

This package provides software-based DPI emulation for gaming mice.
It allows users to simulate different DPI settings from 400 to 26,000 DPI
through software scaling and OS-level adjustments.

Modules:
    - dpi_emulator: Main DPI emulation engine with cross-platform support
"""

from .dpi_emulator import DPIEmulator, DPIConfig, DPIMode, MouseMovement

__all__ = ['DPIEmulator', 'DPIConfig', 'DPIMode', 'MouseMovement']
