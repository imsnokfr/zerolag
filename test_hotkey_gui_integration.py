#!/usr/bin/env python3
"""
Test suite for hotkey GUI integration.

This module tests the integration of hotkey functionality with the PyQt5 GUI,
including hotkey management, profile switching, and emergency controls.
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.main_window import ZeroLagMainWindow


class TestHotkeyGUIIntegration(unittest.TestCase):
    """Test hotkey GUI integration functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        # Mock the input handlers to avoid initialization issues
        with patch('src.gui.main_window.InputHandler'), \
             patch('src.gui.main_window.GamingMouseHandler'), \
             patch('src.gui.main_window.GamingKeyboardHandler'), \
             patch('src.gui.main_window.PerformanceMonitor'):
            
            self.window = ZeroLagMainWindow()
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'window'):
            self.window.close()
    
    def test_hotkey_tab_creation(self):
        """Test that hotkey tab is created properly."""
        # Check if hotkey tab exists
        from PyQt5.QtWidgets import QTabWidget
        tab_widget = self.window.findChild(QTabWidget)
        self.assertIsNotNone(tab_widget)
        
        # Check if hotkey tab is present
        tab_count = tab_widget.count()
        self.assertGreaterEqual(tab_count, 4)  # Should have at least 4 tabs including hotkeys
        
        # Find hotkey tab
        hotkey_tab_found = False
        for i in range(tab_count):
            if tab_widget.tabText(i) == "Hotkeys":
                hotkey_tab_found = True
                break
        
        self.assertTrue(hotkey_tab_found, "Hotkeys tab not found")
    
    def test_hotkey_controls_exist(self):
        """Test that all hotkey controls are created."""
        # Check profile combo
        self.assertIsNotNone(self.window.hotkey_profile_combo)
        self.assertIsNotNone(self.window.hotkey_preset_combo)
        
        # Check hotkey input controls
        self.assertIsNotNone(self.window.modifier_combo)
        self.assertIsNotNone(self.window.key_combo)
        self.assertIsNotNone(self.window.action_combo)
        
        # Check buttons
        self.assertIsNotNone(self.window.add_hotkey_btn)
        self.assertIsNotNone(self.window.remove_hotkey_btn)
        self.assertIsNotNone(self.window.clear_hotkeys_btn)
        self.assertIsNotNone(self.window.test_hotkey_btn)
        
        # Check emergency controls
        self.assertIsNotNone(self.window.emergency_stop_combo)
        self.assertIsNotNone(self.window.emergency_reset_combo)
        self.assertIsNotNone(self.window.disable_all_combo)
        self.assertIsNotNone(self.window.emergency_status_label)
        
        # Check control buttons
        self.assertIsNotNone(self.window.start_hotkeys_btn)
        self.assertIsNotNone(self.window.stop_hotkeys_btn)
    
    def test_hotkey_profile_management(self):
        """Test hotkey profile management functionality."""
        # Test profile combo has default items
        profile_items = [self.window.hotkey_profile_combo.itemText(i) 
                        for i in range(self.window.hotkey_profile_combo.count())]
        self.assertIn("Default", profile_items)
        self.assertIn("FPS", profile_items)
        self.assertIn("MOBA", profile_items)
        self.assertIn("RTS", profile_items)
        self.assertIn("Custom", profile_items)
        
        # Test preset combo has expected items
        preset_items = [self.window.hotkey_preset_combo.itemText(i) 
                       for i in range(self.window.hotkey_preset_combo.count())]
        self.assertIn("FPS", preset_items)
        self.assertIn("MOBA", preset_items)
        self.assertIn("RTS", preset_items)
        self.assertIn("MMO", preset_items)
        self.assertIn("Productivity", preset_items)
        self.assertIn("Custom", preset_items)
    
    def test_hotkey_input_controls(self):
        """Test hotkey input controls."""
        # Test modifier combo
        modifier_items = [self.window.modifier_combo.itemText(i) 
                         for i in range(self.window.modifier_combo.count())]
        expected_modifiers = ["None", "Ctrl", "Alt", "Shift", "Ctrl+Alt", 
                             "Ctrl+Shift", "Alt+Shift", "Ctrl+Alt+Shift"]
        for modifier in expected_modifiers:
            self.assertIn(modifier, modifier_items)
        
        # Test key combo
        key_items = [self.window.key_combo.itemText(i) 
                    for i in range(self.window.key_combo.count())]
        expected_keys = ["F1", "F2", "Space", "Enter", "Esc", "Delete"]
        for key in expected_keys:
            self.assertIn(key, key_items)
        
        # Test action combo
        action_items = [self.window.action_combo.itemText(i) 
                       for i in range(self.window.action_combo.count())]
        expected_actions = ["Profile Switch", "DPI Increase", "DPI Decrease", 
                           "Emergency Stop", "Emergency Reset", "Disable All"]
        for action in expected_actions:
            self.assertIn(action, action_items)
    
    def test_emergency_hotkey_controls(self):
        """Test emergency hotkey controls."""
        # Test emergency stop combo
        stop_items = [self.window.emergency_stop_combo.itemText(i) 
                     for i in range(self.window.emergency_stop_combo.count())]
        expected_stop = ["Ctrl+Alt+Esc", "Ctrl+Shift+Esc", "Alt+F4", "Ctrl+Alt+Q"]
        for stop in expected_stop:
            self.assertIn(stop, stop_items)
        
        # Test emergency reset combo
        reset_items = [self.window.emergency_reset_combo.itemText(i) 
                      for i in range(self.window.emergency_reset_combo.count())]
        expected_reset = ["Ctrl+Alt+R", "Ctrl+Shift+R", "Alt+R", "Ctrl+Alt+Z"]
        for reset in expected_reset:
            self.assertIn(reset, reset_items)
        
        # Test disable all combo
        disable_items = [self.window.disable_all_combo.itemText(i) 
                        for i in range(self.window.disable_all_combo.count())]
        expected_disable = ["Ctrl+Alt+D", "Ctrl+Shift+D", "Alt+D", "Ctrl+Alt+X"]
        for disable in expected_disable:
            self.assertIn(disable, disable_items)
    
    def test_hotkey_initialization(self):
        """Test hotkey system initialization."""
        # Check that hotkey managers are initialized
        self.assertIsNotNone(self.window.hotkey_config_manager)
        self.assertIsNotNone(self.window.hotkey_preset_manager)
        
        # Check that hotkey list is initialized
        self.assertIsNotNone(self.window.hotkey_list)
        self.assertTrue(self.window.hotkey_list.isReadOnly())
    
    def test_hotkey_button_states(self):
        """Test initial hotkey button states."""
        # Start button should be enabled initially
        self.assertTrue(self.window.start_hotkeys_btn.isEnabled())
        
        # Stop button should be disabled initially
        self.assertFalse(self.window.stop_hotkeys_btn.isEnabled())
        
        # Emergency status should show ready
        self.assertEqual(self.window.emergency_status_label.text(), "Status: Ready")
    
    def test_hotkey_profile_changed_signal(self):
        """Test hotkey profile change signal connection."""
        # This tests that the signal is connected (no exception should be raised)
        try:
            self.window.hotkey_profile_combo.currentTextChanged.emit("FPS")
        except Exception as e:
            self.fail(f"Profile change signal failed: {e}")
    
    def test_hotkey_preset_changed_signal(self):
        """Test hotkey preset change signal connection."""
        # This tests that the signal is connected (no exception should be raised)
        try:
            self.window.hotkey_preset_combo.currentTextChanged.emit("FPS")
        except Exception as e:
            self.fail(f"Preset change signal failed: {e}")
    
    def test_hotkey_button_connections(self):
        """Test that hotkey buttons are properly connected."""
        # Test that clicking buttons doesn't raise exceptions
        try:
            self.window.add_hotkey_btn.clicked.emit()
            self.window.remove_hotkey_btn.clicked.emit()
            self.window.clear_hotkeys_btn.clicked.emit()
            self.window.test_hotkey_btn.clicked.emit()
            self.window.start_hotkeys_btn.clicked.emit()
            self.window.stop_hotkeys_btn.clicked.emit()
        except Exception as e:
            self.fail(f"Button click failed: {e}")
    
    def test_hotkey_list_display(self):
        """Test hotkey list display functionality."""
        # Check that hotkey list is not empty (default config has bindings)
        hotkey_text = self.window.hotkey_list.toPlainText()
        self.assertNotEqual(hotkey_text, "")
        # Should contain some hotkey bindings
        self.assertIn("->", hotkey_text)
    
    def test_emergency_status_display(self):
        """Test emergency status display."""
        # Should start with "Ready" status
        self.assertEqual(self.window.emergency_status_label.text(), "Status: Ready")
        
        # Should have green color initially
        style_sheet = self.window.emergency_status_label.styleSheet()
        self.assertIn("color: #4CAF50", style_sheet)
        self.assertIn("font-weight: bold", style_sheet)
    
    def test_hotkey_control_styling(self):
        """Test hotkey control styling."""
        # Start button should have green background
        start_style = self.window.start_hotkeys_btn.styleSheet()
        self.assertIn("background-color: #4CAF50", start_style)
        
        # Stop button should have red background
        stop_style = self.window.stop_hotkeys_btn.styleSheet()
        self.assertIn("background-color: #f44336", stop_style)
    
    def test_hotkey_tab_layout(self):
        """Test hotkey tab layout structure."""
        # Find the hotkey tab widget
        from PyQt5.QtWidgets import QTabWidget, QGroupBox
        tab_widget = self.window.findChild(QTabWidget)
        self.assertIsNotNone(tab_widget, "Hotkey tab widget not found")
        
        # Check that hotkey tab has proper layout
        hotkey_tab_index = -1
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == "Hotkeys":
                hotkey_tab_index = i
                break
        
        self.assertGreaterEqual(hotkey_tab_index, 0, "Hotkeys tab not found")
        hotkey_widget = tab_widget.widget(hotkey_tab_index)
        self.assertIsNotNone(hotkey_widget)
        
        # Check for group boxes
        group_boxes = hotkey_widget.findChildren(QGroupBox)
        group_titles = [gb.title() for gb in group_boxes]
        
        expected_groups = ["Hotkey Profiles", "Hotkey Bindings", "Emergency Hotkeys"]
        for group in expected_groups:
            self.assertIn(group, group_titles, f"Group box '{group}' not found")


def run_hotkey_gui_tests():
    """Run all hotkey GUI integration tests."""
    print("=" * 60)
    print("HOTKEY GUI INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHotkeyGUIIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("HOTKEY GUI INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_hotkey_gui_tests()
    sys.exit(0 if success else 1)
