#!/usr/bin/env python3
"""
Test script for the ZeroLag Profile Management System

This script demonstrates and tests the profile management functionality
including profile creation, switching, validation, and import/export.

Usage:
    python test_profile_system.py [--test-type <type>] [--cleanup]
    
Test Types:
    - basic: Basic profile operations
    - presets: Gaming mode presets
    - validation: Profile validation
    - import_export: Import/export functionality
    - performance: Performance testing
    - integration: Integration with system components
    - all: Run all tests (default)
"""

import sys
import time
import threading
import argparse
import tempfile
import shutil
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

try:
    from core.profiles import (
        Profile, ProfileManager, GamingModePresets, ProfileValidator, ProfileExporter,
        GamingMode, DPISettings, PollingSettings, KeyboardSettings, SmoothingSettings,
        MacroSettings, PerformanceSettings, GUISettings, HotkeySettings, ProfileSettings,
        ProfileMetadata, ExportFormat, ImportResult, ValidationResult
    )
    print("✅ All profile system imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class TestType(Enum):
    BASIC = "basic"
    PRESETS = "presets"
    VALIDATION = "validation"
    IMPORT_EXPORT = "import_export"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    ALL = "all"

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    error: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None

class ProfileSystemTester:
    """Comprehensive tester for the profile management system"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.manager: Optional[ProfileManager] = None
        self.validator: Optional[ProfileValidator] = None
        self.exporter: Optional[ProfileExporter] = None
        self.test_dir: Optional[Path] = None
        
    def setup(self) -> bool:
        """Set up the testing environment"""
        try:
            print("🔧 Setting up profile system test environment...")
            
            # Create temporary test directory
            self.test_dir = Path(tempfile.mkdtemp(prefix="zerolag_profile_test_"))
            print(f"📁 Test directory: {self.test_dir}")
            
            # Create profile manager with test configuration
            from core.profiles.profile_manager import ProfileManagerConfig
            config = ProfileManagerConfig(
                profiles_directory=str(self.test_dir / "profiles"),
                backup_directory=str(self.test_dir / "backups"),
                auto_save=True,
                auto_save_interval=5.0
            )
            self.manager = ProfileManager(config)
            
            # Create validator and exporter
            self.validator = ProfileValidator()
            self.exporter = ProfileExporter(self.validator)
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test environment"""
        try:
            if self.manager:
                self.manager.cleanup()
            if self.test_dir and self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            print("🧹 Test environment cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Run a single test and record results"""
        print(f"\n🧪 Running test: {test_name}")
        start_time = time.time()
        
        try:
            stats = test_func()
            duration = time.time() - start_time
            print(f"✅ {test_name} completed in {duration:.3f}s")
            return TestResult(test_name, True, duration, stats=stats)
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_name} failed: {e}")
            return TestResult(test_name, False, duration, error=str(e))
    
    def test_basic_operations(self) -> Dict[str, Any]:
        """Test basic profile operations"""
        print("  📝 Testing basic profile operations...")
        
        # Create profiles
        profiles_created = 0
        for i in range(3):
            profile_name = f"Test Profile {i+1}"
            success = self.manager.create_profile(
                profile_name, 
                f"Test profile {i+1} for validation",
                GamingMode.FPS if i == 0 else GamingMode.MOBA
            )
            if success:
                profiles_created += 1
        
        print(f"  📊 Created {profiles_created} profiles")
        
        # List profiles
        profile_list = self.manager.list_profiles()
        print(f"  📋 Found {len(profile_list)} profiles: {profile_list}")
        
        # Switch between profiles
        switches = 0
        for profile_name in profile_list:
            if self.manager.switch_profile(profile_name):
                switches += 1
                active = self.manager.get_active_profile()
                if active:
                    print(f"  🔄 Switched to: {active.metadata.name}")
        
        # Test profile modification
        if profile_list:
            profile = self.manager.get_profile(profile_list[0])
            if profile:
                original_dpi = profile.settings.dpi.dpi_value
                profile.settings.dpi.dpi_value = 1600
                profile.update_modified_time()
                
                # Save profile
                save_success = self.manager.save_profile(profile_list[0])
                print(f"  💾 Profile save successful: {save_success}")
                
                # Restore original value
                profile.settings.dpi.dpi_value = original_dpi
        
        # Test profile deletion
        deleted = 0
        if len(profile_list) > 1:
            # Keep first profile, delete others
            for profile_name in profile_list[1:]:
                if self.manager.delete_profile(profile_name, create_backup=True):
                    deleted += 1
        
        print(f"  🗑️ Deleted {deleted} profiles")
        
        # Get final statistics
        final_stats = self.manager.get_stats()
        
        return {
            "profiles_created": profiles_created,
            "profiles_switched": switches,
            "profiles_deleted": deleted,
            "total_profiles": final_stats.total_profiles,
            "storage_usage_mb": final_stats.storage_usage_mb
        }
    
    def test_gaming_presets(self) -> Dict[str, Any]:
        """Test gaming mode presets"""
        print("  🎮 Testing gaming mode presets...")
        
        # Get all presets
        presets = GamingModePresets.get_all_presets()
        print(f"  📋 Available presets: {list(presets.keys())}")
        
        # Create profiles from presets
        created_profiles = 0
        for preset_name, preset_profile in presets.items():
            # Create a copy with unique name
            custom_name = f"Custom {preset_name}"
            success = self.manager.create_profile(
                custom_name,
                f"Custom profile based on {preset_name}",
                preset_profile.metadata.gaming_mode
            )
            
            if success:
                # Apply preset settings
                profile = self.manager.get_profile(custom_name)
                if profile:
                    # Copy settings from preset
                    profile.settings = preset_profile.settings
                    profile.update_modified_time()
                    self.manager.save_profile(custom_name)
                    created_profiles += 1
                    
                    print(f"  ✅ Created {custom_name} ({preset_profile.metadata.gaming_mode.value})")
        
        # Test preset-specific settings
        fps_profile = self.manager.get_profile("Custom FPS Mode")
        if fps_profile:
            print(f"  🎯 FPS Profile - DPI: {fps_profile.settings.dpi.dpi_value}, "
                  f"Mouse Polling: {fps_profile.settings.polling.mouse_polling_rate}Hz")
        
        moba_profile = self.manager.get_profile("Custom MOBA Mode")
        if moba_profile:
            print(f"  ⚔️ MOBA Profile - DPI: {moba_profile.settings.dpi.dpi_value}, "
                  f"Smoothing: {moba_profile.settings.smoothing.enabled}")
        
        # Test profile switching between presets
        switches = 0
        for profile_name in self.manager.list_profiles():
            if profile_name.startswith("Custom "):
                if self.manager.switch_profile(profile_name):
                    switches += 1
        
        return {
            "presets_available": len(presets),
            "profiles_created": created_profiles,
            "preset_switches": switches
        }
    
    def test_validation(self) -> Dict[str, Any]:
        """Test profile validation"""
        print("  ✅ Testing profile validation...")
        
        # Create valid profile
        valid_profile = Profile()
        valid_profile.metadata.name = "Valid Profile"
        valid_profile.metadata.gaming_mode = GamingMode.FPS
        valid_profile.settings.dpi.dpi_value = 1600
        valid_profile.settings.polling.mouse_polling_rate = 8000
        
        valid_result = self.validator.validate_profile(valid_profile)
        print(f"  ✅ Valid profile validation: {valid_result.is_valid}")
        
        # Create invalid profile
        invalid_profile = Profile()
        invalid_profile.metadata.name = ""  # Invalid: empty name
        invalid_profile.settings.dpi.dpi_value = 50000  # Invalid: out of range
        invalid_profile.settings.polling.mouse_polling_rate = 50  # Invalid: too low
        
        invalid_result = self.validator.validate_profile(invalid_profile)
        print(f"  ❌ Invalid profile validation: {valid_result.is_valid}")
        print(f"  📊 Validation errors: {len(invalid_result.errors)}")
        
        # Test file validation
        test_file = self.test_dir / "test_profile.json"
        valid_profile.save_to_file(test_file)
        
        file_result = self.validator.validate_profile_file(test_file)
        print(f"  📁 File validation: {file_result.is_valid}")
        
        # Test validation scores
        scores = {
            "compatibility": valid_result.compatibility_score,
            "performance": valid_result.performance_score,
            "security": valid_result.security_score
        }
        
        return {
            "valid_profile_valid": valid_result.is_valid,
            "invalid_profile_valid": invalid_result.is_valid,
            "validation_errors": len(invalid_result.errors),
            "file_validation": file_result.is_valid,
            "validation_scores": scores
        }
    
    def test_import_export(self) -> Dict[str, Any]:
        """Test import/export functionality"""
        print("  📤 Testing import/export functionality...")
        
        # Create test profile
        test_profile = Profile()
        test_profile.metadata.name = "Export Test Profile"
        test_profile.metadata.description = "Profile for testing import/export"
        test_profile.metadata.gaming_mode = GamingMode.FPS
        test_profile.settings.dpi.dpi_value = 1600
        test_profile.settings.polling.mouse_polling_rate = 8000
        
        # Export to JSON
        json_file = self.test_dir / "test_profile.json"
        json_success = self.exporter.export_profile(test_profile, json_file, ExportFormat.JSON)
        print(f"  📄 JSON export: {json_success}")
        
        # Export to ZIP
        zip_file = self.test_dir / "test_profile.zip"
        zip_success = self.exporter.export_profile(test_profile, zip_file, ExportFormat.ZIP)
        print(f"  📦 ZIP export: {zip_success}")
        
        # Import from JSON
        json_result = self.exporter.import_profile(json_file, validate=True)
        print(f"  📥 JSON import: {json_result.success}")
        
        # Import from ZIP
        zip_result = self.exporter.import_profile(zip_file, validate=True)
        print(f"  📥 ZIP import: {zip_result.success}")
        
        # Test multiple profile export
        profiles = [test_profile]
        multi_zip_file = self.test_dir / "multiple_profiles.zip"
        multi_success = self.exporter.export_profiles(profiles, multi_zip_file, ExportFormat.ZIP)
        print(f"  📦 Multiple profiles export: {multi_success}")
        
        # Test multiple profile import
        multi_results = self.exporter.import_profiles(multi_zip_file, validate=True)
        print(f"  📥 Multiple profiles import: {len(multi_results)} profiles")
        
        # Test export info
        json_info = self.exporter.get_export_info(json_file)
        zip_info = self.exporter.get_export_info(zip_file)
        
        return {
            "json_export": json_success,
            "zip_export": zip_success,
            "json_import": json_result.success,
            "zip_import": zip_result.success,
            "multi_export": multi_success,
            "multi_import_count": len(multi_results),
            "json_info_available": json_info is not None,
            "zip_info_available": zip_info is not None
        }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test profile system performance"""
        print("  ⚡ Testing profile system performance...")
        
        # Test profile creation performance
        start_time = time.time()
        profiles_created = 0
        
        for i in range(50):
            profile_name = f"Performance Test Profile {i+1}"
            if self.manager.create_profile(profile_name, f"Performance test {i+1}", GamingMode.FPS):
                profiles_created += 1
        
        creation_time = time.time() - start_time
        print(f"  📊 Created {profiles_created} profiles in {creation_time:.3f}s")
        
        # Test profile switching performance
        profile_list = self.manager.list_profiles()
        switch_start = time.time()
        switches = 0
        
        for profile_name in profile_list[:10]:  # Test first 10 profiles
            if self.manager.switch_profile(profile_name):
                switches += 1
        
        switch_time = time.time() - switch_start
        print(f"  🔄 Switched {switches} profiles in {switch_time:.3f}s")
        
        # Test validation performance
        validation_start = time.time()
        validations = 0
        
        for profile_name in profile_list[:10]:
            profile = self.manager.get_profile(profile_name)
            if profile:
                result = self.validator.validate_profile(profile)
                validations += 1
        
        validation_time = time.time() - validation_start
        print(f"  ✅ Validated {validations} profiles in {validation_time:.3f}s")
        
        # Test export performance
        export_start = time.time()
        exports = 0
        
        for profile_name in profile_list[:5]:  # Test first 5 profiles
            profile = self.manager.get_profile(profile_name)
            if profile:
                export_file = self.test_dir / f"export_{profile_name}.json"
                if self.exporter.export_profile(profile, export_file, ExportFormat.JSON):
                    exports += 1
        
        export_time = time.time() - export_start
        print(f"  📤 Exported {exports} profiles in {export_time:.3f}s")
        
        return {
            "profiles_created": profiles_created,
            "creation_time": creation_time,
            "profiles_per_second": profiles_created / creation_time if creation_time > 0 else 0,
            "switches_performed": switches,
            "switch_time": switch_time,
            "validations_performed": validations,
            "validation_time": validation_time,
            "exports_performed": exports,
            "export_time": export_time
        }
    
    def test_integration(self) -> Dict[str, Any]:
        """Test integration with system components"""
        print("  🔗 Testing integration with system components...")
        
        # Create a test profile
        test_profile = Profile()
        test_profile.metadata.name = "Integration Test Profile"
        test_profile.metadata.gaming_mode = GamingMode.FPS
        test_profile.settings.dpi.dpi_value = 1600
        test_profile.settings.polling.mouse_polling_rate = 8000
        test_profile.settings.keyboard.nkro_enabled = True
        
        # Test profile application (simulated)
        print("  🎯 Testing profile application...")
        
        # Simulate applying profile to system components
        class MockInputHandler:
            def set_polling_mode(self, mode): pass
            def set_mouse_polling_rate(self, rate): pass
            def set_keyboard_polling_rate(self, rate): pass
        
        class MockMouseHandler:
            def set_dpi_mode(self, mode): pass
            def set_dpi_value(self, value): pass
            def set_sensitivity(self, value): pass
        
        class MockKeyboardHandler:
            def set_nkro_mode(self, enabled): pass
            def set_rapid_trigger(self, enabled): pass
            def set_debounce(self, enabled): pass
        
        class MockGUIApp:
            def apply_profile_settings(self, settings): pass
        
        # Test profile application
        mock_input = MockInputHandler()
        mock_mouse = MockMouseHandler()
        mock_keyboard = MockKeyboardHandler()
        mock_gui = MockGUIApp()
        
        apply_success = test_profile.apply_to_system(
            mock_input, mock_mouse, mock_keyboard, mock_gui
        )
        print(f"  ✅ Profile application: {apply_success}")
        
        # Test profile summary
        summary = test_profile.get_summary()
        print(f"  📊 Profile summary: {summary['name']} - {summary['gaming_mode']}")
        
        # Test profile cloning
        cloned_profile = test_profile.clone("Cloned Integration Profile")
        print(f"  📋 Profile cloning: {cloned_profile.metadata.name}")
        
        # Test profile checksum validation
        checksum_valid = test_profile.validate_checksum()
        print(f"  🔐 Checksum validation: {checksum_valid}")
        
        return {
            "profile_application": apply_success,
            "profile_summary": summary is not None,
            "profile_cloning": cloned_profile is not None,
            "checksum_validation": checksum_valid
        }
    
    def run_all_tests(self, test_types: List[TestType]) -> List[TestResult]:
        """Run all specified tests"""
        print("🚀 Starting ZeroLag Profile System Tests")
        print("=" * 50)
        
        if not self.setup():
            return []
        
        try:
            if TestType.BASIC in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_basic_operations, "Basic Profile Operations"))
            
            if TestType.PRESETS in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_gaming_presets, "Gaming Mode Presets"))
            
            if TestType.VALIDATION in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_validation, "Profile Validation"))
            
            if TestType.IMPORT_EXPORT in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_import_export, "Import/Export Functionality"))
            
            if TestType.PERFORMANCE in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_performance, "Performance Testing"))
            
            if TestType.INTEGRATION in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_integration, "Integration Testing"))
            
        finally:
            self.cleanup()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        if total_tests > 0:
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        else:
            print("Success Rate: N/A (no tests run)")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.error}")
        
        print("\n📈 Performance Stats:")
        for result in self.results:
            if result.success and result.stats:
                print(f"  {result.test_name}:")
                for key, value in result.stats.items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.3f}")
                    else:
                        print(f"    {key}: {value}")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="ZeroLag Profile System Tester")
    parser.add_argument("--test-type", choices=[t.value for t in TestType], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up test files after completion")
    
    args = parser.parse_args()
    
    # Convert string to enum
    test_type = TestType(args.test_type)
    test_types = [test_type] if test_type != TestType.ALL else [TestType.ALL]
    
    # Run tests
    tester = ProfileSystemTester()
    results = tester.run_all_tests(test_types)
    tester.print_summary()
    
    # Exit with appropriate code
    failed_tests = sum(1 for r in results if not r.success)
    sys.exit(failed_tests)

if __name__ == "__main__":
    main()
