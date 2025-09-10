#!/usr/bin/env python3
"""
Simple Emergency Hotkey Test

This script tests basic emergency hotkey functionality.
"""

import sys
import os
import time
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_emergency():
    """Test basic emergency functionality."""
    print("Testing basic emergency functionality...")
    
    try:
        from src.core.hotkeys.emergency_hotkeys import EmergencyHotkeyManager, EmergencyConfig, EmergencyState
        print("✓ Emergency modules imported successfully")
        
        # Test initialization
        config = EmergencyConfig()
        config.require_confirmation = False
        config.auto_recovery_enabled = False
        
        manager = EmergencyHotkeyManager(config)
        print("✓ EmergencyHotkeyManager created")
        
        # Test basic state
        assert manager.current_state == EmergencyState.NORMAL
        assert not manager.is_emergency_state()
        print("✓ Initial state correct")
        
        # Test stats
        stats = manager.get_emergency_stats()
        assert stats.total_emergency_actions == 0
        print("✓ Initial stats correct")
        
        print("✓ Basic emergency test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic emergency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_emergency()
    sys.exit(0 if success else 1)
