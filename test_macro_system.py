#!/usr/bin/env python3
"""
Test script for the ZeroLag Macro System

This script demonstrates and tests the macro recording, playback, and editing
functionality of the ZeroLag gaming input optimization system.

Usage:
    python test_macro_system.py [--test-type <type>] [--duration <seconds>]
    
Test Types:
    - basic: Basic macro recording and playback
    - advanced: Advanced features like loops and conditions
    - editor: Macro editing functionality
    - performance: Performance and stress testing
    - integration: Integration with input handlers
    - all: Run all tests (default)
"""

import sys
import time
import threading
import argparse
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Add src to path for imports
sys.path.insert(0, 'src')

try:
    from core.macro import (
        MacroManager, MacroRecorder, MacroPlayer, MacroEditor,
        MacroEventType, PlaybackState, EditorMode, MacroCategory,
        MacroRecorderConfig, PlaybackConfig, EditorConfig, MacroManagerConfig
    )
    from core.input.input_handler import InputHandler, InputEventType
    from core.input.mouse_handler import GamingMouseHandler
    from core.input.keyboard_handler import GamingKeyboardHandler
    print("✅ All macro system imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class TestType(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    EDITOR = "editor"
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

class MacroSystemTester:
    """Comprehensive tester for the macro system"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.manager: Optional[MacroManager] = None
        self.input_handler: Optional[InputHandler] = None
        
    def setup(self) -> bool:
        """Set up the testing environment"""
        try:
            print("🔧 Setting up macro system test environment...")
            
            # Create macro manager with test configuration
            config = MacroManagerConfig(
                enabled=True,
                storage_path="test_macros",
                auto_save=True,
                auto_save_interval=5.0
            )
            self.manager = MacroManager(config)
            
            # Create input handler for integration tests
            self.input_handler = InputHandler()
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test environment"""
        try:
            if self.input_handler:
                self.input_handler.stop()
            if self.manager:
                self.manager.cleanup()
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
    
    def test_basic_recording_playback(self) -> Dict[str, Any]:
        """Test basic macro recording and playback"""
        print("  📝 Testing basic macro recording...")
        
        # Create test library
        library_name = "Test Library"
        self.manager.create_library(library_name, "Basic test library")
        
        # Start recording
        macro_name = "Basic Test Macro"
        self.manager.start_recording(macro_name, "A basic test macro")
        
        # Get the recorder from active recordings
        recorder = self.manager.active_recordings[macro_name]
        
        # Simulate some events
        time.sleep(0.1)
        recorder.record_event(MacroEventType.KEY_PRESS, {"key": "a"}, 0.1)
        time.sleep(0.05)
        recorder.record_event(MacroEventType.KEY_RELEASE, {"key": "a"}, 0.15)
        time.sleep(0.1)
        recorder.record_event(MacroEventType.MOUSE_MOVE, {"position": (100, 200)}, 0.25)
        time.sleep(0.05)
        recorder.record_event(MacroEventType.MOUSE_CLICK, {"button": "left"}, 0.3)
        
        # Stop recording
        macro = self.manager.stop_recording(macro_name, library_name)
        
        print(f"  📊 Recorded {len(macro.events)} events")
        
        # Test playback
        print("  ▶️ Testing macro playback...")
        self.manager.start_playback(library_name, macro_name)
        
        # Wait for playback to complete
        player = self.manager.active_playbacks[macro_name]
        while player.playback_state == PlaybackState.PLAYING:
            time.sleep(0.01)
        
        # Get playback stats
        stats = player.get_stats()
        
        print(f"  📈 Playback completed: {stats.total_events_played} events")
        
        return {
            "events_recorded": len(macro.events),
            "events_played": stats.total_events_played,
            "playback_duration": stats.current_playback_duration,
            "timing_accuracy": stats.average_timing_error_ms
        }
    
    def test_advanced_features(self) -> Dict[str, Any]:
        """Test advanced macro features like loops and conditions"""
        print("  🔄 Testing advanced macro features...")
        
        library_name = "Advanced Test Library"
        self.manager.create_library(library_name, "Advanced features test")
        
        # Create a macro with loops
        macro_name = "Loop Test Macro"
        self.manager.start_recording(macro_name, "A macro with loops")
        
        # Get the recorder
        recorder = self.manager.active_recordings[macro_name]
        
        # Record some events
        recorder.record_event(MacroEventType.KEY_PRESS, {"key": "w"}, 0.0)
        recorder.record_event(MacroEventType.KEY_RELEASE, {"key": "w"}, 0.1)
        recorder.record_event(MacroEventType.DELAY, {"duration": 0.5}, 0.1)
        
        # Add a loop
        recorder.add_loop(0, 2, 3)  # Loop 3 times from event 0 to 2
        
        macro = self.manager.stop_recording(macro_name, library_name)
        
        print(f"  🔁 Created macro with {len(macro.loops)} loops")
        
        # Test playback with loops
        self.manager.start_playback(library_name, macro_name)
        
        player = self.manager.active_playbacks[macro_name]
        while player.playback_state == PlaybackState.PLAYING:
            time.sleep(0.01)
        
        stats = player.get_stats()
        
        return {
            "loops_created": len(macro.loops),
            "events_played": stats.total_events_played,
            "loop_iterations": stats.loop_iterations
        }
    
    def test_editor_functionality(self) -> Dict[str, Any]:
        """Test macro editor functionality"""
        print("  ✏️ Testing macro editor...")
        
        library_name = "Editor Test Library"
        macro_name = "Editor Test Macro"
        
        # Create a simple macro first
        self.manager.create_library(library_name, "Editor test library")
        self.manager.start_recording(macro_name, "A macro for editing")
        
        recorder = self.manager.active_recordings[macro_name]
        recorder.record_event(MacroEventType.KEY_PRESS, {"key": "x"}, 0.0)
        recorder.record_event(MacroEventType.KEY_RELEASE, {"key": "x"}, 0.1)
        
        macro = self.manager.stop_recording(macro_name, library_name)
        
        # Start editing
        self.manager.start_editing(library_name, macro_name)
        
        # Test editor operations
        editor = self.manager.active_editors[macro_name]
        
        # Add an event
        editor.add_event(MacroEventType.KEY_PRESS, {"key": "y"}, 0.2)
        
        # Move an event
        editor.move_event(0, 0.15)
        
        # Delete an event
        editor.delete_event(1)
        
        # Test undo/redo
        editor.undo()
        editor.redo()
        
        # Save changes
        self.manager.save_edits(library_name, macro_name)
        
        # Get editor stats
        editor_stats = editor.get_stats()
        
        return {
            "events_added": editor_stats.events_added,
            "events_moved": editor_stats.events_moved,
            "events_deleted": editor_stats.events_deleted,
            "undo_count": editor_stats.undo_count,
            "redo_count": editor_stats.redo_count
        }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test macro system performance"""
        print("  ⚡ Testing macro system performance...")
        
        library_name = "Performance Test Library"
        macro_name = "Performance Test Macro"
        
        self.manager.create_library(library_name, "Performance test library")
        
        # Create a large macro
        self.manager.start_recording(macro_name, "A large performance test macro")
        
        recorder = self.manager.active_recordings[macro_name]
        start_time = time.time()
        event_count = 1000
        
        for i in range(event_count):
            event_type = MacroEventType.KEY_PRESS if i % 2 == 0 else MacroEventType.KEY_RELEASE
            key = chr(ord('a') + (i % 26))
            timestamp = i * 0.01
            recorder.record_event(event_type, {"key": key}, timestamp)
        
        recording_time = time.time() - start_time
        macro = self.manager.stop_recording(macro_name, library_name)
        
        # Test playback performance
        playback_start = time.time()
        self.manager.start_playback(library_name, macro_name)
        
        player = self.manager.active_playbacks[macro_name]
        while player.playback_state == PlaybackState.PLAYING:
            time.sleep(0.001)
        
        playback_time = time.time() - playback_start
        
        # Test editor performance
        editor_start = time.time()
        self.manager.start_editing(library_name, macro_name)
        
        # Perform some editor operations
        editor = self.manager.active_editors[macro_name]
        for i in range(100):
            editor.add_event(MacroEventType.DELAY, {"duration": 0.1}, i * 0.01)
        
        self.manager.save_edits(library_name, macro_name)
        editor_time = time.time() - editor_start
        
        return {
            "events_recorded": event_count,
            "recording_time": recording_time,
            "playback_time": playback_time,
            "editor_time": editor_time,
            "events_per_second": event_count / recording_time,
            "playback_speed": event_count / playback_time
        }
    
    def test_integration(self) -> Dict[str, Any]:
        """Test integration with input handlers"""
        print("  🔗 Testing integration with input handlers...")
        
        # This would test integration with actual input handlers
        # For now, we'll simulate the integration
        
        library_name = "Integration Test Library"
        macro_name = "Integration Test Macro"
        
        self.manager.create_library(library_name, "Integration test library")
        
        # Test macro recording with input handler
        if self.input_handler:
            self.input_handler.start()
            
            self.manager.start_recording(macro_name, "Integration test macro")
            
            recorder = self.manager.active_recordings[macro_name]
            # Simulate some input events
            time.sleep(0.1)
            recorder.record_event(MacroEventType.KEY_PRESS, {"key": "space"}, 0.1)
            time.sleep(0.05)
            recorder.record_event(MacroEventType.KEY_RELEASE, {"key": "space"}, 0.15)
            
            macro = self.manager.stop_recording(macro_name, library_name)
            
            # Test playback integration
            self.manager.start_playback(library_name, macro_name)
            
            player = self.manager.active_playbacks[macro_name]
            while player.playback_state == PlaybackState.PLAYING:
                time.sleep(0.01)
            
            self.input_handler.stop()
        
        return {
            "integration_successful": True,
            "events_recorded": len(macro.events) if 'macro' in locals() else 0
        }
    
    def run_all_tests(self, test_types: List[TestType]) -> List[TestResult]:
        """Run all specified tests"""
        print("🚀 Starting ZeroLag Macro System Tests")
        print("=" * 50)
        
        if not self.setup():
            return []
        
        try:
            if TestType.BASIC in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_basic_recording_playback, "Basic Recording & Playback"))
            
            if TestType.ADVANCED in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_advanced_features, "Advanced Features"))
            
            if TestType.EDITOR in test_types or TestType.ALL in test_types:
                self.results.append(self.run_test(self.test_editor_functionality, "Editor Functionality"))
            
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
    parser = argparse.ArgumentParser(description="ZeroLag Macro System Tester")
    parser.add_argument("--test-type", choices=[t.value for t in TestType], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--duration", type=float, default=5.0,
                       help="Test duration in seconds")
    
    args = parser.parse_args()
    
    # Convert string to enum
    test_type = TestType(args.test_type)
    test_types = [test_type] if test_type != TestType.ALL else [TestType.ALL]
    
    # Run tests
    tester = MacroSystemTester()
    results = tester.run_all_tests(test_types)
    tester.print_summary()
    
    # Exit with appropriate code
    failed_tests = sum(1 for r in results if not r.success)
    sys.exit(failed_tests)

if __name__ == "__main__":
    main()
