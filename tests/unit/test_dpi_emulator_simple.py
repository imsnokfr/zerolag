#!/usr/bin/env python3
"""
Simple unit tests for DPI emulator algorithms.

Tests the actual methods available in the DPI emulator.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from src.core.dpi.dpi_emulator import DPIEmulator, DPIMode


class TestDPIEmulatorSimple:
    """Simple test cases for DPI emulator algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dpi_emulator = DPIEmulator(enable_logging=False)
    
    def test_initialization(self):
        """Test DPI emulator initialization."""
        assert self.dpi_emulator.get_current_dpi() == 800
        assert self.dpi_emulator.get_scaling_factor() == 1.0
    
    def test_set_dpi_valid_range(self):
        """Test setting DPI within valid range (400-26000)."""
        # Test minimum DPI
        result = self.dpi_emulator.set_dpi(400)
        assert result is True
        assert self.dpi_emulator.get_current_dpi() == 400
        
        # Test maximum DPI
        result = self.dpi_emulator.set_dpi(26000)
        assert result is True
        assert self.dpi_emulator.get_current_dpi() == 26000
        
        # Test middle range
        result = self.dpi_emulator.set_dpi(1600)
        assert result is True
        assert self.dpi_emulator.get_current_dpi() == 1600
    
    def test_set_dpi_invalid_range(self):
        """Test setting DPI outside valid range."""
        # Test below minimum
        result = self.dpi_emulator.set_dpi(399)
        assert result is False
        assert self.dpi_emulator.get_current_dpi() == 800  # Should remain unchanged
        
        # Test above maximum
        result = self.dpi_emulator.set_dpi(26001)
        assert result is False
        assert self.dpi_emulator.get_current_dpi() == 800  # Should remain unchanged
    
    def test_set_mode(self):
        """Test setting different DPI modes."""
        # Test SOFTWARE mode (should always work)
        result = self.dpi_emulator.set_mode(DPIMode.SOFTWARE)
        assert result is True
        
        # Test HYBRID mode (may not be supported on all platforms)
        result = self.dpi_emulator.set_mode(DPIMode.HYBRID)
        # Don't assert True/False as it depends on platform support
        
        # Test NATIVE mode (may not be supported on all platforms)
        result = self.dpi_emulator.set_mode(DPIMode.NATIVE)
        # Don't assert True/False as it depends on platform support
    
    def test_set_smoothing(self):
        """Test setting smoothing enabled/disabled."""
        # Test disabling smoothing
        self.dpi_emulator.set_smoothing(False)
        # No return value, just test it doesn't crash
        
        # Test enabling smoothing
        self.dpi_emulator.set_smoothing(True)
        # No return value, just test it doesn't crash
    
    def test_set_precision_mode(self):
        """Test setting precision mode."""
        # Test enabling precision mode
        self.dpi_emulator.set_precision_mode(True)
        # No return value, just test it doesn't crash
        
        # Test disabling precision mode
        self.dpi_emulator.set_precision_mode(False)
        # No return value, just test it doesn't crash
    
    def test_process_movement(self):
        """Test movement processing."""
        # Test basic movement processing
        dx, dy = self.dpi_emulator.process_movement(10, 20)
        assert isinstance(dx, (int, float))
        assert isinstance(dy, (int, float))
        
        # Test negative values
        dx, dy = self.dpi_emulator.process_movement(-5, -10)
        assert isinstance(dx, (int, float))
        assert isinstance(dy, (int, float))
        
        # Test zero values
        dx, dy = self.dpi_emulator.process_movement(0, 0)
        assert isinstance(dx, (int, float))
        assert isinstance(dy, (int, float))
    
    def test_get_scaling_factor(self):
        """Test getting scaling factor."""
        # Test normal scaling
        self.dpi_emulator.set_dpi(1600)
        factor = self.dpi_emulator.get_scaling_factor()
        assert factor == 2.0  # 1600 / 800
        
        # Test minimum DPI
        self.dpi_emulator.set_dpi(400)
        factor = self.dpi_emulator.get_scaling_factor()
        assert factor == 0.5  # 400 / 800
        
        # Test maximum DPI
        self.dpi_emulator.set_dpi(26000)
        factor = self.dpi_emulator.get_scaling_factor()
        assert factor == 32.5  # 26000 / 800
    
    def test_get_current_dpi(self):
        """Test getting current DPI."""
        self.dpi_emulator.set_dpi(1600)
        assert self.dpi_emulator.get_current_dpi() == 1600
        
        self.dpi_emulator.set_dpi(400)
        assert self.dpi_emulator.get_current_dpi() == 400
    
    def test_start_stop_lifecycle(self):
        """Test DPI emulator start/stop lifecycle."""
        # Test starting
        result = self.dpi_emulator.start()
        assert result is True
        
        # Test stopping
        result = self.dpi_emulator.stop()
        assert result is True
    
    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        stats = self.dpi_emulator.get_performance_stats()
        assert isinstance(stats, dict)
        assert 'total_movements_processed' in stats
        assert 'total_movements_scaled' in stats
        assert 'avg_scaling_factor' in stats
        assert 'current_dpi' in stats
        assert 'base_dpi' in stats
        assert 'scaling_factor' in stats
        assert 'mode' in stats
        assert 'smoothing_enabled' in stats
        assert 'precision_mode' in stats
        assert 'is_active' in stats
    
    def test_callback_registration(self):
        """Test callback registration."""
        # Test movement callback
        movement_callback = Mock()
        self.dpi_emulator.set_movement_callback(movement_callback)
        # No return value, just test it doesn't crash
        
        # Test DPI change callback
        dpi_callback = Mock()
        self.dpi_emulator.set_dpi_change_callback(dpi_callback)
        # No return value, just test it doesn't crash
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test very small movements
        dx, dy = self.dpi_emulator.process_movement(0.1, 0.1)
        assert isinstance(dx, (int, float))
        assert isinstance(dy, (int, float))
        
        # Test very large movements
        dx, dy = self.dpi_emulator.process_movement(10000, 10000)
        assert isinstance(dx, (int, float))
        assert isinstance(dy, (int, float))
        
        # Test fractional DPI values
        self.dpi_emulator.set_dpi(1200)
        factor = self.dpi_emulator.get_scaling_factor()
        assert factor == 1.5  # 1200 / 800
    
    def test_performance_characteristics(self):
        """Test performance characteristics of DPI algorithms."""
        import time
        
        # Test movement processing performance
        start_time = time.time()
        for _ in range(1000):
            self.dpi_emulator.process_movement(10, 10)
        end_time = time.time()
        
        # Should be very fast (less than 0.1 seconds for 1000 operations)
        assert (end_time - start_time) < 0.1
        
        # Test statistics calculation performance
        start_time = time.time()
        for _ in range(1000):
            self.dpi_emulator.get_performance_stats()
        end_time = time.time()
        
        # Should be very fast
        assert (end_time - start_time) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
