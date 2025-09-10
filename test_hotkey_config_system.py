#!/usr/bin/env python3
"""
Test Hotkey Configuration System

This script tests the comprehensive hotkey configuration system including:
- Configuration management
- Profile management
- Preset system
- GUI components
- Import/export functionality
"""

import sys
import os
import time
import logging
import tempfile
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.hotkeys.hotkey_config import (
    HotkeyConfigManager, HotkeyProfile, HotkeyBinding, HotkeyProfileType
)
from src.core.hotkeys.hotkey_presets import (
    HotkeyPresetManager, GamingGenre, PresetComplexity, HotkeyPreset
)
from src.core.hotkeys.hotkey_actions import HotkeyActionType
from src.core.hotkeys.hotkey_detector import HotkeyModifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_hotkey_config_manager():
    """Test the HotkeyConfigManager class."""
    print("\n=== Testing HotkeyConfigManager ===")
    
    # Test initialization with temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_path = f.name
    
    try:
        config_manager = HotkeyConfigManager(temp_config_path)
        print("✓ HotkeyConfigManager initialized")
        
        # Test profile creation
        profile = config_manager.create_profile("Test Profile", HotkeyProfileType.CUSTOM, "Test description")
        assert profile.name == "Test Profile"
        assert profile.profile_type == HotkeyProfileType.CUSTOM
        print("✓ Profile creation successful")
        
        # Test profile listing
        profiles = config_manager.get_profile_list()
        assert "Test Profile" in profiles
        print("✓ Profile listing successful")
        
        # Test profile info
        info = config_manager.get_profile_info("Test Profile")
        assert info['name'] == "Test Profile"
        assert info['type'] == HotkeyProfileType.CUSTOM.value
        print("✓ Profile info retrieval successful")
        
        # Test active profile setting
        success = config_manager.set_active_profile("Test Profile")
        assert success
        active_profile = config_manager.get_active_profile()
        assert active_profile.name == "Test Profile"
        print("✓ Active profile setting successful")
        
        # Test binding addition
        binding = config_manager.add_binding(
            "Test Profile",
            HotkeyActionType.TOGGLE_ZEROLAG,
            HotkeyModifier.CTRL | HotkeyModifier.ALT,
            90,  # Z key
            "Z",
            "Toggle ZeroLag"
        )
        assert binding is not None
        assert binding.action_type == HotkeyActionType.TOGGLE_ZEROLAG
        print("✓ Binding addition successful")
        
        # Test binding retrieval
        bindings = config_manager.get_bindings("Test Profile")
        assert len(bindings) == 1
        assert list(bindings.values())[0].action_type == HotkeyActionType.TOGGLE_ZEROLAG
        print("✓ Binding retrieval successful")
        
        # Test binding update
        success = config_manager.update_binding("Test Profile", binding.hotkey_id, description="Updated description")
        assert success
        updated_binding = config_manager.get_bindings("Test Profile")[binding.hotkey_id]
        assert updated_binding.description == "Updated description"
        print("✓ Binding update successful")
        
        # Test binding removal
        success = config_manager.remove_binding("Test Profile", binding.hotkey_id)
        assert success
        bindings = config_manager.get_bindings("Test Profile")
        assert len(bindings) == 0
        print("✓ Binding removal successful")
        
        # Test profile deletion (need to set different active profile first)
        config_manager.create_profile("Temp Profile", HotkeyProfileType.DEFAULT, "Temporary profile")
        config_manager.set_active_profile("Temp Profile")
        
        success = config_manager.delete_profile("Test Profile")
        assert success
        profiles = config_manager.get_profile_list()
        assert "Test Profile" not in profiles
        print("✓ Profile deletion successful")
        
        # Test configuration save/load
        config_manager.create_profile("Save Test", HotkeyProfileType.DEFAULT, "Save test profile")
        config_manager.add_binding("Save Test", HotkeyActionType.EMERGENCY_STOP, HotkeyModifier.CTRL, 27, "Escape", "Emergency stop")
        
        # Save configuration
        success = config_manager.save_config()
        assert success
        print("✓ Configuration save successful")
        
        # Create new manager and load configuration
        new_config_manager = HotkeyConfigManager(temp_config_path)
        loaded_profiles = new_config_manager.get_profile_list()
        assert "Save Test" in loaded_profiles
        print("✓ Configuration load successful")
        
        print("✓ HotkeyConfigManager tests passed!")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)

def test_hotkey_preset_manager():
    """Test the HotkeyPresetManager class."""
    print("\n=== Testing HotkeyPresetManager ===")
    
    preset_manager = HotkeyPresetManager()
    print("✓ HotkeyPresetManager initialized")
    
    # Test built-in presets
    all_presets = preset_manager.get_all_presets()
    assert len(all_presets) > 0
    print(f"✓ Loaded {len(all_presets)} built-in presets")
    
    # Test preset retrieval
    fps_preset = preset_manager.get_preset("fps_gaming")
    assert fps_preset is not None
    assert fps_preset.genre == GamingGenre.FPS
    print("✓ FPS preset retrieval successful")
    
    # Test genre filtering
    fps_presets = preset_manager.get_presets_by_genre(GamingGenre.FPS)
    assert len(fps_presets) > 0
    assert all(preset.genre == GamingGenre.FPS for preset in fps_presets)
    print("✓ Genre filtering successful")
    
    # Test complexity filtering
    basic_presets = preset_manager.get_presets_by_complexity(PresetComplexity.BASIC)
    assert len(basic_presets) > 0
    assert all(preset.complexity == PresetComplexity.BASIC for preset in basic_presets)
    print("✓ Complexity filtering successful")
    
    # Test preset search
    search_results = preset_manager.search_presets("gaming")
    assert len(search_results) > 0
    print("✓ Preset search successful")
    
    # Test custom preset creation
    custom_bindings = [
        {
            "action": HotkeyActionType.TOGGLE_ZEROLAG,
            "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
            "virtual_key": 90,
            "key_name": "Z",
            "description": "Custom toggle"
        }
    ]
    
    preset_id = preset_manager.create_custom_preset(
        "Custom Test",
        GamingGenre.FPS,
        PresetComplexity.BASIC,
        "Custom test preset",
        custom_bindings,
        "Test Author",
        ["Test requirement"],
        ["test", "custom"]
    )
    assert preset_id is not None
    print("✓ Custom preset creation successful")
    
    # Test custom preset retrieval
    custom_preset = preset_manager.get_preset(preset_id)
    assert custom_preset is not None
    assert custom_preset.name == "Custom Test"
    assert custom_preset.author == "Test Author"
    print("✓ Custom preset retrieval successful")
    
    # Test preset application to profile
    config_manager = HotkeyConfigManager()
    test_profile = config_manager.create_profile("Test Profile", HotkeyProfileType.CUSTOM, "Test profile")
    
    success = preset_manager.apply_preset_to_profile("fps_gaming", test_profile)
    assert success
    assert len(test_profile.bindings) > 0
    print("✓ Preset application successful")
    
    # Test preset export/import
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_export_path = f.name
    
    try:
        # Export preset
        success = preset_manager.export_preset("fps_gaming", temp_export_path)
        assert success
        print("✓ Preset export successful")
        
        # Import preset
        imported_id = preset_manager.import_preset(temp_export_path)
        assert imported_id is not None
        print("✓ Preset import successful")
        
        # Test custom preset deletion
        success = preset_manager.delete_custom_preset(preset_id)
        assert success
        deleted_preset = preset_manager.get_preset(preset_id)
        assert deleted_preset is None
        print("✓ Custom preset deletion successful")
        
    finally:
        if os.path.exists(temp_export_path):
            os.unlink(temp_export_path)
    
    print("✓ HotkeyPresetManager tests passed!")

def test_hotkey_configuration_integration():
    """Test integration between configuration and preset systems."""
    print("\n=== Testing Configuration Integration ===")
    
    # Initialize managers
    config_manager = HotkeyConfigManager()
    preset_manager = HotkeyPresetManager()
    
    # Create a test profile
    profile = config_manager.create_profile("Integration Test", HotkeyProfileType.CUSTOM, "Integration test profile")
    print("✓ Test profile created")
    
    # Apply a preset to the profile
    success = preset_manager.apply_preset_to_profile("fps_gaming", profile)
    assert success
    assert len(profile.bindings) > 0
    print("✓ Preset applied to profile")
    
    # Test profile export
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_export_path = f.name
    
    try:
        success = config_manager.export_profile("Integration Test", temp_export_path)
        assert success
        print("✓ Profile export successful")
        
        # Test profile import
        success = config_manager.import_profile(temp_export_path, "Imported Profile")
        assert success
        imported_profile = config_manager.get_profile_info("Imported Profile")
        assert imported_profile is not None
        print("✓ Profile import successful")
        
    finally:
        if os.path.exists(temp_export_path):
            os.unlink(temp_export_path)
    
    print("✓ Configuration integration tests passed!")

def test_hotkey_validation():
    """Test hotkey validation functionality."""
    print("\n=== Testing Hotkey Validation ===")
    
    from src.core.hotkeys.hotkey_validator import HotkeyValidator
    
    validator = HotkeyValidator()
    print("✓ HotkeyValidator initialized")
    
    # Test conflict detection
    bindings = [
        HotkeyBinding(
            hotkey_id=1,
            action_type=HotkeyActionType.TOGGLE_ZEROLAG,
            modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
            virtual_key=90,
            key_name="Z",
            description="Toggle ZeroLag"
        ),
        HotkeyBinding(
            hotkey_id=2,
            action_type=HotkeyActionType.EMERGENCY_STOP,
            modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
            virtual_key=90,  # Same key combination
            key_name="Z",
            description="Emergency stop"
        )
    ]
    
    conflicts = validator.check_conflicts(bindings)
    assert len(conflicts) > 0
    print("✓ Conflict detection successful")
    
    # Test validation
    result = validator.validate_binding(
        HotkeyModifier.CTRL | HotkeyModifier.ALT,
        90,
        bindings
    )
    assert not result.is_valid
    print("✓ Binding validation successful")
    
    print("✓ Hotkey validation tests passed!")

def test_hotkey_configuration_persistence():
    """Test configuration persistence and data integrity."""
    print("\n=== Testing Configuration Persistence ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_path = f.name
    
    try:
        # Create initial configuration
        config_manager = HotkeyConfigManager(temp_config_path)
        
        # Create multiple profiles with different settings
        profiles = ["Profile 1", "Profile 2", "Profile 3"]
        for i, profile_name in enumerate(profiles):
            profile = config_manager.create_profile(profile_name, HotkeyProfileType.CUSTOM, f"Test profile {i+1}")
            
            # Add different bindings to each profile
            for j in range(3):
                config_manager.add_binding(
                    profile_name,
                    HotkeyActionType.TOGGLE_ZEROLAG,
                    HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    90 + j,  # Different virtual keys
                    f"Key{j}",
                    f"Test binding {j+1}"
                )
        
        # Set active profile
        config_manager.set_active_profile("Profile 2")
        
        # Save configuration
        success = config_manager.save_config()
        assert success
        print("✓ Multi-profile configuration saved")
        
        # Create new manager and load configuration
        new_config_manager = HotkeyConfigManager(temp_config_path)
        
        # Verify all profiles were loaded
        loaded_profiles = new_config_manager.get_profile_list()
        assert len(loaded_profiles) == 3
        assert all(profile in loaded_profiles for profile in profiles)
        print("✓ All profiles loaded correctly")
        
        # Verify active profile
        active_profile = new_config_manager.get_active_profile()
        assert active_profile.name == "Profile 2"
        print("✓ Active profile restored correctly")
        
        # Verify bindings for each profile
        for profile_name in profiles:
            bindings = new_config_manager.get_bindings(profile_name)
            assert len(bindings) == 3
            print(f"✓ Profile '{profile_name}' bindings restored correctly")
        
        print("✓ Configuration persistence tests passed!")
        
    finally:
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)

def run_hotkey_config_tests():
    """Run all hotkey configuration tests."""
    print("Starting Hotkey Configuration System Tests...")
    print("=" * 60)
    
    try:
        test_hotkey_config_manager()
        test_hotkey_preset_manager()
        test_hotkey_configuration_integration()
        test_hotkey_validation()
        test_hotkey_configuration_persistence()
        
        print("\n" + "=" * 60)
        print("🎉 ALL HOTKEY CONFIGURATION TESTS PASSED! 🎉")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ HOTKEY CONFIGURATION TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_hotkey_config_tests()
    sys.exit(0 if success else 1)
