"""
DPI Emulation System for ZeroLag

This module provides software-based DPI emulation for gaming mice.
It intercepts mouse movement events and applies scaling factors to simulate
different DPI settings from 400 to 26,000 DPI.

Features:
- Real-time DPI adjustment (400-26000 range)
- Smooth scaling with sub-pixel precision
- Cross-platform support (Windows, macOS, Linux)
- Performance optimized for gaming
- Integration with input handlers
"""

import time
import threading
import math
from typing import Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

# Platform-specific imports
import platform
if platform.system() == "Windows":
    try:
        import win32api
        import win32con
        import win32gui
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
else:
    WINDOWS_AVAILABLE = False


class DPIMode(Enum):
    """DPI emulation modes."""
    SOFTWARE = "software"  # Pure software scaling
    HYBRID = "hybrid"      # Software + OS cursor sensitivity
    NATIVE = "native"      # Use hardware DPI (no emulation)


@dataclass
class DPIConfig:
    """DPI configuration settings."""
    target_dpi: int = 800
    base_dpi: int = 800  # Hardware DPI
    mode: DPIMode = DPIMode.SOFTWARE
    smoothing_enabled: bool = True
    acceleration_enabled: bool = False
    precision_mode: bool = False  # Sub-pixel precision


@dataclass
class MouseMovement:
    """Represents a mouse movement event."""
    dx: int
    dy: int
    timestamp: float
    raw_dx: int
    raw_dy: int


class DPIEmulator:
    """
    Software-based DPI emulation system.
    
    This class provides real-time DPI scaling by intercepting mouse movements
    and applying scaling factors to simulate different DPI settings.
    """
    
    def __init__(self, base_dpi: int = 800, enable_logging: bool = True):
        """
        Initialize the DPI emulator.
        
        Args:
            base_dpi: The hardware DPI of the mouse
            enable_logging: Enable debug logging
        """
        self.base_dpi = base_dpi
        self.logger = None
        if enable_logging:
            import logging
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
        
        # Configuration
        self.config = DPIConfig(base_dpi=base_dpi)
        self.is_active = False
        self._lock = threading.Lock()
        
        # Movement tracking
        self.movement_history: list = []
        self.max_history_size = 100
        self.last_movement_time = 0.0
        
        # Performance metrics
        self.total_movements_processed = 0
        self.total_movements_scaled = 0
        self.avg_scaling_factor = 1.0
        self.last_performance_update = time.time()
        
        # Callbacks
        self.movement_callback: Optional[Callable] = None
        self.dpi_change_callback: Optional[Callable] = None
        
        # Platform-specific settings
        self.platform = platform.system()
        self._init_platform_specific()
        
    def _init_platform_specific(self):
        """Initialize platform-specific components."""
        if self.platform == "Windows" and WINDOWS_AVAILABLE:
            self._init_windows()
        elif self.platform == "Darwin":  # macOS
            self._init_macos()
        elif self.platform == "Linux":
            self._init_linux()
        else:
            if self.logger:
                self.logger.warning(f"Unsupported platform: {self.platform}")
    
    def _init_windows(self):
        """Initialize Windows-specific components."""
        try:
            # Get current cursor sensitivity
            self.original_sensitivity = win32api.SystemParametersInfo(
                win32con.SPI_GETMOUSESPEED, 0, 0
            )
            if self.logger:
                self.logger.info(f"Windows: Original cursor sensitivity: {self.original_sensitivity}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Windows initialization error: {e}")
    
    def _init_macos(self):
        """Initialize macOS-specific components."""
        try:
            # macOS cursor sensitivity is typically handled through system preferences
            # We'll use software scaling primarily
            if self.logger:
                self.logger.info("macOS: Using software DPI emulation")
        except Exception as e:
            if self.logger:
                self.logger.error(f"macOS initialization error: {e}")
    
    def _init_linux(self):
        """Initialize Linux-specific components."""
        try:
            # Linux cursor sensitivity can be adjusted via xinput
            # We'll use software scaling primarily
            if self.logger:
                self.logger.info("Linux: Using software DPI emulation")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Linux initialization error: {e}")
    
    def set_dpi(self, target_dpi: int) -> bool:
        """
        Set the target DPI for emulation.
        
        Args:
            target_dpi: Target DPI (400-26000)
            
        Returns:
            True if successful, False otherwise
        """
        if not 400 <= target_dpi <= 26000:
            if self.logger:
                self.logger.error(f"Invalid DPI: {target_dpi}. Must be between 400-26000")
            return False
        
        with self._lock:
            old_dpi = self.config.target_dpi
            self.config.target_dpi = target_dpi
            
            # Apply platform-specific adjustments
            success = self._apply_dpi_settings()
            
            if success:
                if self.logger:
                    self.logger.info(f"DPI changed from {old_dpi} to {target_dpi}")
                
                # Notify callback
                if self.dpi_change_callback:
                    try:
                        self.dpi_change_callback(target_dpi, old_dpi)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"DPI change callback error: {e}")
            else:
                # Revert on failure
                self.config.target_dpi = old_dpi
                
        return success
    
    def _apply_dpi_settings(self) -> bool:
        """Apply DPI settings based on the current mode."""
        try:
            if self.config.mode == DPIMode.SOFTWARE:
                return self._apply_software_dpi()
            elif self.config.mode == DPIMode.HYBRID:
                return self._apply_hybrid_dpi()
            elif self.config.mode == DPIMode.NATIVE:
                return self._apply_native_dpi()
            else:
                return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error applying DPI settings: {e}")
            return False
    
    def _apply_software_dpi(self) -> bool:
        """Apply pure software DPI scaling."""
        # Software scaling is handled in the movement processing
        # No system-level changes needed
        return True
    
    def _apply_hybrid_dpi(self) -> bool:
        """Apply hybrid DPI (software + OS sensitivity)."""
        if self.platform == "Windows" and WINDOWS_AVAILABLE:
            try:
                # Calculate scaling factor
                scaling_factor = self.config.target_dpi / self.config.base_dpi
                
                # Adjust Windows cursor sensitivity
                # Windows sensitivity range is 1-20, default is 10
                new_sensitivity = max(1, min(20, int(10 * scaling_factor)))
                
                win32api.SystemParametersInfo(
                    win32con.SPI_SETMOUSESPEED, 0, new_sensitivity
                )
                
                if self.logger:
                    self.logger.info(f"Windows: Set cursor sensitivity to {new_sensitivity}")
                return True
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Windows sensitivity adjustment error: {e}")
                return False
        else:
            # Fall back to software scaling
            return self._apply_software_dpi()
    
    def _apply_native_dpi(self) -> bool:
        """Apply native DPI (no emulation)."""
        if self.platform == "Windows" and WINDOWS_AVAILABLE:
            try:
                # Restore original sensitivity
                win32api.SystemParametersInfo(
                    win32con.SPI_SETMOUSESPEED, 0, self.original_sensitivity
                )
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Windows native DPI error: {e}")
                return False
        return True
    
    def process_movement(self, dx: int, dy: int) -> Tuple[int, int]:
        """
        Process a mouse movement and apply DPI scaling.
        
        Args:
            dx: Raw X movement
            dy: Raw Y movement
            
        Returns:
            Tuple of (scaled_dx, scaled_dy)
        """
        if not self.is_active or self.config.mode == DPIMode.NATIVE:
            return dx, dy
        
        current_time = time.time()
        
        # Calculate scaling factor
        scaling_factor = self.config.target_dpi / self.config.base_dpi
        
        # Apply smoothing if enabled
        if self.config.smoothing_enabled:
            dx, dy = self._apply_smoothing(dx, dy, scaling_factor)
        else:
            # Direct scaling
            dx = int(dx * scaling_factor)
            dy = int(dy * scaling_factor)
        
        # Track movement for performance metrics
        self._track_movement(dx, dy, current_time)
        
        # Update performance metrics
        self.total_movements_processed += 1
        self.total_movements_scaled += 1
        self.avg_scaling_factor = scaling_factor
        
        # Notify callback
        if self.movement_callback:
            try:
                movement = MouseMovement(
                    dx=dx, dy=dy, timestamp=current_time,
                    raw_dx=int(dx / scaling_factor), raw_dy=int(dy / scaling_factor)
                )
                self.movement_callback(movement)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Movement callback error: {e}")
        
        return dx, dy
    
    def _apply_smoothing(self, dx: int, dy: int, scaling_factor: float) -> Tuple[int, int]:
        """Apply smoothing to mouse movements."""
        # Add movement to history
        self.movement_history.append((dx, dy, time.time()))
        
        # Keep history size manageable
        if len(self.movement_history) > self.max_history_size:
            self.movement_history.pop(0)
        
        # Calculate smoothed movement
        if len(self.movement_history) >= 3:
            # Use weighted average of last 3 movements
            weights = [0.1, 0.3, 0.6]  # More weight to recent movements
            smoothed_dx = 0
            smoothed_dy = 0
            
            for i, (hist_dx, hist_dy, _) in enumerate(self.movement_history[-3:]):
                weight = weights[i]
                smoothed_dx += hist_dx * weight
                smoothed_dy += hist_dy * weight
            
            dx = int(smoothed_dx * scaling_factor)
            dy = int(smoothed_dy * scaling_factor)
        else:
            # Not enough history, use direct scaling
            dx = int(dx * scaling_factor)
            dy = int(dy * scaling_factor)
        
        return dx, dy
    
    def _track_movement(self, dx: int, dy: int, timestamp: float):
        """Track movement for performance analysis."""
        self.last_movement_time = timestamp
        
        # Update performance metrics periodically
        if timestamp - self.last_performance_update > 1.0:  # Every second
            self._update_performance_metrics()
            self.last_performance_update = timestamp
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        # This could be expanded to track more detailed metrics
        pass
    
    def start(self) -> bool:
        """Start the DPI emulator."""
        with self._lock:
            if self.is_active:
                return True
            
            try:
                self.is_active = True
                if self.logger:
                    self.logger.info(f"DPI emulator started (target: {self.config.target_dpi} DPI)")
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error starting DPI emulator: {e}")
                return False
    
    def stop(self) -> bool:
        """Stop the DPI emulator."""
        with self._lock:
            if not self.is_active:
                return True
            
            try:
                self.is_active = False
                
                # Restore original settings
                if self.config.mode == DPIMode.HYBRID and self.platform == "Windows" and WINDOWS_AVAILABLE:
                    try:
                        win32api.SystemParametersInfo(
                            win32con.SPI_SETMOUSESPEED, 0, self.original_sensitivity
                        )
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Error restoring Windows sensitivity: {e}")
                
                if self.logger:
                    self.logger.info("DPI emulator stopped")
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping DPI emulator: {e}")
                return False
    
    def get_current_dpi(self) -> int:
        """Get the current target DPI."""
        return self.config.target_dpi
    
    def get_scaling_factor(self) -> float:
        """Get the current scaling factor."""
        return self.config.target_dpi / self.config.base_dpi
    
    def set_mode(self, mode: DPIMode) -> bool:
        """Set the DPI emulation mode."""
        with self._lock:
            old_mode = self.config.mode
            self.config.mode = mode
            
            # Apply new mode
            success = self._apply_dpi_settings()
            
            if success:
                if self.logger:
                    self.logger.info(f"DPI mode changed from {old_mode.value} to {mode.value}")
            else:
                # Revert on failure
                self.config.mode = old_mode
            
            return success
    
    def set_smoothing(self, enabled: bool):
        """Enable or disable movement smoothing."""
        self.config.smoothing_enabled = enabled
        if self.logger:
            self.logger.info(f"Movement smoothing {'enabled' if enabled else 'disabled'}")
    
    def set_precision_mode(self, enabled: bool):
        """Enable or disable precision mode (sub-pixel accuracy)."""
        self.config.precision_mode = enabled
        if self.logger:
            self.logger.info(f"Precision mode {'enabled' if enabled else 'disabled'}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        current_time = time.time()
        
        return {
            "is_active": self.is_active,
            "current_dpi": self.config.target_dpi,
            "base_dpi": self.config.base_dpi,
            "scaling_factor": self.get_scaling_factor(),
            "mode": self.config.mode.value,
            "smoothing_enabled": self.config.smoothing_enabled,
            "precision_mode": self.config.precision_mode,
            "total_movements_processed": self.total_movements_processed,
            "total_movements_scaled": self.total_movements_scaled,
            "avg_scaling_factor": self.avg_scaling_factor,
            "last_movement_time": self.last_movement_time,
            "time_since_last_movement": current_time - self.last_movement_time if self.last_movement_time > 0 else 0,
            "platform": self.platform
        }
    
    def set_movement_callback(self, callback: Callable[[MouseMovement], None]):
        """Set callback for processed movements."""
        self.movement_callback = callback
    
    def set_dpi_change_callback(self, callback: Callable[[int, int], None]):
        """Set callback for DPI changes."""
        self.dpi_change_callback = callback
