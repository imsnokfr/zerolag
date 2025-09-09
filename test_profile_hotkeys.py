#!/usr/bin/env python3
"""
Test script for Profile Switching Hotkeys

This script tests the profile switching hotkey functionality,
including hotkey registration, profile switching, and visual feedback.

Usage:
    python test_profile_hotkeys.py
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.hotkeys import HotkeyManager, HotkeyManagerConfig
from core.hotkeys.profile_hotkeys import ProfileHotkeyManager, ProfileHotkeyConfig
from core.hotkeys.profile_feedback import ProfileFeedbackManager, FeedbackConfig, FeedbackStyle, ConsoleFeedback
from core.profiles import ProfileManager, ProfileManagerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProfileHotkeyTester:
    """Test class for profile switching hotkeys."""
    
    def __init__(self):
        self.hotkey_manager = None
        self.profile_manager = None
        self.profile_hotkey_manager = None
        self.feedback_manager = None
        self.console_feedback = None
        self.test_results = []
        
    def setup(self):
        """Set up the test environment."""
        try:
            logger.info("Setting up profile hotkey test environment...")
            
            # Initialize profile manager
            profile_config = ProfileManagerConfig()
            self.profile_manager = ProfileManager(profile_config)
            
            # Create some test profiles
            self._create_test_profiles()
            
            # Initialize hotkey manager
            hotkey_config = HotkeyManagerConfig(
                enable_hotkeys=True,
                auto_start=False,  # We'll start manually
                log_hotkey_events=True
            )
            self.hotkey_manager = HotkeyManager(hotkey_config)
            
            # Initialize profile hotkey manager
            profile_hotkey_config = ProfileHotkeyConfig(
                enable_profile_cycling=True,
                enable_specific_switching=True,
                enable_preset_switching=True,
                visual_feedback_duration=2.0
            )
            self.profile_hotkey_manager = ProfileHotkeyManager(
                self.profile_manager, 
                profile_hotkey_config
            )
            
            # Initialize feedback manager
            feedback_config = FeedbackConfig(
                style=FeedbackStyle.NOTIFICATION,
                duration=2.0,
                show_profile_name=True,
                show_switch_time=True,
                show_success_status=True
            )
            self.feedback_manager = ProfileFeedbackManager(feedback_config)
            
            # Initialize console feedback
            self.console_feedback = ConsoleFeedback()
            
            # Connect feedback
            self.profile_hotkey_manager.add_feedback_callback(self._on_profile_switch)
            
            logger.info("Test environment setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up test environment: {e}")
            return False
    
    def _create_test_profiles(self):
        """Create test profiles for testing."""
        try:
            # Create FPS profile
            fps_profile = self.profile_manager.create_profile(
                "FPS Gaming",
                "Optimized for first-person shooter games"
            )
            if fps_profile:
                logger.info("Created FPS profile")
            
            # Create MOBA profile
            moba_profile = self.profile_manager.create_profile(
                "MOBA Gaming", 
                "Optimized for MOBA games"
            )
            if moba_profile:
                logger.info("Created MOBA profile")
            
            # Create RTS profile
            rts_profile = self.profile_manager.create_profile(
                "RTS Gaming",
                "Optimized for real-time strategy games"
            )
            if rts_profile:
                logger.info("Created RTS profile")
            
            # Create Productivity profile
            prod_profile = self.profile_manager.create_profile(
                "Productivity",
                "Optimized for productivity tasks"
            )
            if prod_profile:
                logger.info("Created Productivity profile")
            
            logger.info(f"Created {len(self.profile_manager.profiles)} test profiles")
            
        except Exception as e:
            logger.error(f"Error creating test profiles: {e}")
    
    def _on_profile_switch(self, feedback):
        """Handle profile switch feedback."""
        logger.info(f"Profile switch feedback: {feedback.profile_name} - {'Success' if feedback.success else 'Failed'}")
        
        # Show console feedback
        self.console_feedback.show_feedback(feedback)
        
        # Record test result
        self.test_results.append({
            'profile_name': feedback.profile_name,
            'success': feedback.success,
            'switch_time': feedback.switch_time,
            'timestamp': time.time()
        })
    
    def test_hotkey_registration(self):
        """Test hotkey registration."""
        logger.info("Testing hotkey registration...")
        
        try:
            # Start hotkey manager
            if not self.hotkey_manager.start():
                logger.error("Failed to start hotkey manager")
                return False
            
            # Register profile hotkeys
            hotkey_ids = self.profile_hotkey_manager.register_profile_hotkeys(self.hotkey_manager)
            
            if not hotkey_ids:
                logger.error("No hotkeys registered")
                return False
            
            logger.info(f"Registered {len(hotkey_ids)} hotkeys:")
            for name, hotkey_id in hotkey_ids.items():
                logger.info(f"  {name}: {hotkey_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing hotkey registration: {e}")
            return False
    
    def test_profile_switching(self):
        """Test profile switching functionality."""
        logger.info("Testing profile switching...")
        
        try:
            # Test cycle profile
            logger.info("Testing profile cycling...")
            result = self.profile_hotkey_manager._handle_cycle_profile(None)
            logger.info(f"Cycle profile result: {result}")
            
            # Test specific profile switching
            logger.info("Testing specific profile switching...")
            profile_list = self.profile_hotkey_manager.get_profile_list()
            if profile_list:
                result = self.profile_hotkey_manager._handle_switch_to_profile(None, 0)
                logger.info(f"Switch to profile 0 result: {result}")
            
            # Test preset switching
            logger.info("Testing preset switching...")
            result = self.profile_hotkey_manager._handle_switch_to_preset(None, "FPS")
            logger.info(f"Switch to FPS preset result: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing profile switching: {e}")
            return False
    
    def test_feedback_system(self):
        """Test the feedback system."""
        logger.info("Testing feedback system...")
        
        try:
            # Test console feedback
            test_feedback = type('Feedback', (), {
                'profile_name': 'Test Profile',
                'success': True,
                'switch_time': 0.123,
                'message': 'Test feedback message'
            })()
            
            self.console_feedback.show_feedback(test_feedback)
            
            # Test feedback manager
            self.feedback_manager.show_feedback(test_feedback)
            
            logger.info("Feedback system test completed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing feedback system: {e}")
            return False
    
    def test_hotkey_processing(self):
        """Test hotkey processing with simulated events."""
        logger.info("Testing hotkey processing...")
        
        try:
            # Simulate hotkey events
            from core.hotkeys.hotkey_detector import HotkeyEvent, HotkeyModifier, HotkeyType
            
            # Test cycle profile event
            cycle_event = HotkeyEvent(
                hotkey_id=1,
                modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
                virtual_key=ord('P'),
                event_type=HotkeyType.PRESS,
                timestamp=time.time()
            )
            
            # Process the event
            result = self.hotkey_manager._handle_hotkey_event(cycle_event)
            logger.info(f"Processed cycle profile event: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing hotkey processing: {e}")
            return False
    
    def run_interactive_test(self):
        """Run interactive hotkey test."""
        logger.info("Starting interactive hotkey test...")
        logger.info("Press the following hotkeys to test:")
        logger.info("  Ctrl+Alt+P - Cycle through profiles")
        logger.info("  Ctrl+Alt+1 - Switch to profile 1")
        logger.info("  Ctrl+Alt+2 - Switch to profile 2")
        logger.info("  Ctrl+Alt+F - Switch to FPS preset")
        logger.info("  Ctrl+Alt+M - Switch to MOBA preset")
        logger.info("  Ctrl+Alt+R - Switch to RTS preset")
        logger.info("  Ctrl+Alt+O - Switch to MMO preset")
        logger.info("Press Ctrl+C to exit")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Interactive test interrupted by user")
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("Starting profile hotkey tests...")
        
        tests = [
            ("Setup", self.setup),
            ("Hotkey Registration", self.test_hotkey_registration),
            ("Profile Switching", self.test_profile_switching),
            ("Feedback System", self.test_feedback_system),
            ("Hotkey Processing", self.test_hotkey_processing),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} Test ---")
            try:
                if test_func():
                    logger.info(f"✓ {test_name} test passed")
                    passed += 1
                else:
                    logger.error(f"✗ {test_name} test failed")
            except Exception as e:
                logger.error(f"✗ {test_name} test failed with exception: {e}")
        
        logger.info(f"\n--- Test Results ---")
        logger.info(f"Passed: {passed}/{total}")
        logger.info(f"Success rate: {passed/total*100:.1f}%")
        
        if self.test_results:
            logger.info(f"\nProfile switch results:")
            for result in self.test_results:
                status = "✓" if result['success'] else "✗"
                logger.info(f"  {status} {result['profile_name']} ({result['switch_time']:.3f}s)")
        
        return passed == total
    
    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.stop()
                logger.info("Stopped hotkey manager")
            
            logger.info("Test cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main test function."""
    print("Profile Switching Hotkeys Test")
    print("=" * 40)
    
    tester = ProfileHotkeyTester()
    
    try:
        # Run automated tests
        success = tester.run_all_tests()
        
        if success:
            print("\nAll tests passed! Starting interactive test...")
            tester.run_interactive_test()
        else:
            print("\nSome tests failed. Check the logs for details.")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
    
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
