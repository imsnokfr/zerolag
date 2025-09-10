#!/usr/bin/env python3
"""
Test suite for ZeroLag System Tray Integration.

This module tests the system tray functionality including:
- Tray icon creation and display
- Tray menu functionality
- Tray notifications
- Quick access controls
- Profile switching from tray
- DPI controls from tray
- Emergency controls from tray
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QIcon

# Add the src directory to the path
sys.path.insert(0, 'src')

from gui.main_window import ZeroLagMainWindow


class TestSystemTrayIntegration(unittest.TestCase):
    """Test system tray integration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # Mock the input handlers to avoid initialization issues
        with patch('src.gui.main_window.InputHandler'), \
             patch('src.gui.main_window.GamingMouseHandler'), \
             patch('src.gui.main_window.GamingKeyboardHandler'), \
             patch('src.gui.main_window.PerformanceMonitor'), \
             patch('src.gui.main_window.HotkeyManager'), \
             patch('src.gui.main_window.HotkeyConfigManager'), \
             patch('src.gui.main_window.HotkeyPresetManager'), \
             patch('src.gui.main_window.EmergencyHotkeyManager'), \
             patch('src.gui.main_window.EmergencyIntegration'):
            
            self.window = ZeroLagMainWindow()
            
        # Mock the profile manager
        self.window.profile_manager = Mock()
        self.window.profile_manager.get_profiles.return_value = ['Default', 'FPS', 'MOBA']
        
        # Mock the profile combo
        self.window.profile_combo = Mock()
        self.window.profile_combo.currentText.return_value = 'Default'
        self.window.profile_combo.findText.return_value = 0
        self.window.profile_combo.setCurrentIndex = Mock()
        self.window.profile_combo.count.return_value = 3
        self.window.profile_combo.itemText.side_effect = lambda i: ['Default', 'FPS', 'MOBA'][i]
        
        # Mock the DPI slider
        self.window.dpi_slider = Mock()
        self.window.dpi_slider.value.return_value = 1600
        self.window.dpi_slider.setValue = Mock()
        self.window.dpi_slider.maximum.return_value = 26000
        self.window.dpi_slider.minimum.return_value = 400
        
        # Mock other required attributes
        self.window.optimization_running = False
        self.window.notifications_checkbox = Mock()
        self.window.notifications_checkbox.isChecked.return_value = True
        
        # Mock the log_message method
        self.window.log_message = Mock()
        
        # Mock the apply methods
        self.window.apply_profile = Mock()
        self.window.apply_dpi_settings = Mock()
        
        # Mock the start/stop methods
        self.window.start_optimization = Mock()
        self.window.stop_optimization = Mock()
        self.window.start_hotkeys = Mock()
        self.window.stop_hotkeys = Mock()
        
        # Mock the hotkey manager
        self.window.hotkey_manager = Mock()
        self.window.hotkey_manager.is_running.return_value = False
        
        # Mock the save settings method
        self.window.save_settings = Mock()
        
        # Mock the tray icon showMessage method
        if hasattr(self.window, 'tray_icon'):
            self.window.tray_icon.showMessage = Mock()
    
    def setup_tray_mock(self):
        """Set up tray icon mock for testing."""
        if hasattr(self.window, 'tray_icon'):
            self.window.tray_icon.showMessage = Mock()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'window'):
            self.window.close()
    
    def test_system_tray_creation(self):
        """Test that system tray is created properly."""
        # Check if system tray is available
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.window.create_system_tray()
            self.setup_tray_mock()
            
            # Verify tray icon was created
            self.assertIsNotNone(self.window.tray_icon)
            self.assertTrue(self.window.tray_icon.isVisible())
            
            # Verify tray menu was created
            self.assertIsNotNone(self.window.tray_menu)
            
            # Verify update timer was created
            self.assertIsNotNone(self.window.tray_update_timer)
            self.assertTrue(self.window.tray_update_timer.isActive())
        else:
            self.skipTest("System tray not available on this system")
    
    def test_tray_menu_structure(self):
        """Test that tray menu has proper structure."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        self.setup_tray_mock()
        
        # Check that menu has actions
        actions = self.window.tray_menu.actions()
        self.assertGreater(len(actions), 0)
        
        # Check for key menu items
        action_texts = [action.text() for action in actions]
        self.assertIn("ZeroLag - Gaming Input Optimizer", action_texts)
        self.assertIn("Profile: Default", action_texts)
        self.assertIn("DPI: 1600", action_texts)
    
    def test_tray_icon_activation(self):
        """Test tray icon activation handling."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test double-click to show window
        self.window.hide()
        self.window.tray_icon_activated(QSystemTrayIcon.DoubleClick)
        self.assertTrue(self.window.isVisible())
        
        # Test double-click to hide window
        self.window.show()
        self.window.tray_icon_activated(QSystemTrayIcon.DoubleClick)
        self.assertFalse(self.window.isVisible())
    
    def test_profile_switching_from_tray(self):
        """Test profile switching from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test switching to FPS profile
        self.window.switch_profile_from_tray("FPS")
        
        # Verify profile was switched
        self.window.profile_combo.setCurrentIndex.assert_called_with(0)
        self.window.apply_profile.assert_called_once()
        
        # Verify notification was shown
        self.window.tray_icon.showMessage.assert_called_once()
    
    def test_dpi_control_from_tray(self):
        """Test DPI control from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test setting DPI to 3200
        self.window.set_dpi_from_tray(3200)
        
        # Verify DPI was set
        self.window.dpi_slider.setValue.assert_called_with(3200)
        self.window.apply_dpi_settings.assert_called_once()
        
        # Verify notification was shown
        self.window.tray_icon.showMessage.assert_called_once()
    
    def test_dpi_increase_decrease(self):
        """Test DPI increase/decrease from tray."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test DPI increase
        self.window.dpi_slider.value.return_value = 1600
        self.window.increase_dpi_from_tray()
        self.window.dpi_slider.setValue.assert_called_with(1700)
        
        # Test DPI decrease
        self.window.dpi_slider.value.return_value = 1600
        self.window.decrease_dpi_from_tray()
        self.window.dpi_slider.setValue.assert_called_with(1500)
    
    def test_optimization_toggle_from_tray(self):
        """Test optimization toggle from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test starting optimization
        self.window.optimization_running = False
        self.window.toggle_optimization_from_tray()
        self.window.start_optimization.assert_called_once()
        
        # Test stopping optimization
        self.window.optimization_running = True
        self.window.toggle_optimization_from_tray()
        self.window.stop_optimization.assert_called_once()
    
    def test_hotkey_toggle_from_tray(self):
        """Test hotkey toggle from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test starting hotkeys
        self.window.hotkey_manager.is_running.return_value = False
        self.window.toggle_hotkeys_from_tray()
        self.window.start_hotkeys.assert_called_once()
        
        # Test stopping hotkeys
        self.window.hotkey_manager.is_running.return_value = True
        self.window.toggle_hotkeys_from_tray()
        self.window.stop_hotkeys.assert_called_once()
    
    def test_emergency_stop_from_tray(self):
        """Test emergency stop from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        self.window.emergency_stop_from_tray()
        
        # Verify both optimization and hotkeys were stopped
        self.window.stop_optimization.assert_called_once()
        self.window.stop_hotkeys.assert_called_once()
        
        # Verify notification was shown
        self.window.tray_icon.showMessage.assert_called_once()
    
    def test_reset_from_tray(self):
        """Test reset to defaults from tray menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        self.window.reset_from_tray()
        
        # Verify profile was reset
        self.window.profile_combo.setCurrentIndex.assert_called_with(0)
        self.window.apply_profile.assert_called_once()
        
        # Verify DPI was reset
        self.window.dpi_slider.setValue.assert_called_with(1600)
        self.window.apply_dpi_settings.assert_called_once()
        
        # Verify notification was shown
        self.window.tray_icon.showMessage.assert_called_once()
    
    def test_tray_status_updates(self):
        """Test tray status update functionality."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test optimization status update
        self.window.optimization_running = True
        self.window.update_tray_optimization_status()
        
        # Test hotkey status update
        self.window.hotkey_manager.is_running.return_value = True
        self.window.update_tray_hotkey_status()
        
        # Test general status update
        self.window.update_tray_status()
        
        # Verify menu was recreated
        self.assertIsNotNone(self.window.tray_menu)
    
    def test_tray_notifications(self):
        """Test tray notification functionality."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Test profile change notification
        self.window.switch_profile_from_tray("FPS")
        self.window.tray_icon.showMessage.assert_called_with(
            "Profile Changed",
            "Switched to profile: FPS",
            QSystemTrayIcon.Information,
            2000
        )
        
        # Test DPI change notification
        self.window.set_dpi_from_tray(3200)
        self.window.tray_icon.showMessage.assert_called_with(
            "DPI Changed",
            "DPI set to: 3200",
            QSystemTrayIcon.Information,
            2000
        )
    
    def test_close_event_with_tray(self):
        """Test close event handling with tray enabled."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        # Mock minimize to tray checkbox
        self.window.minimize_tray_checkbox = Mock()
        self.window.minimize_tray_checkbox.isChecked.return_value = True
        
        # Test close event with minimize to tray enabled
        from PyQt5.QtCore import QEvent
        event = QEvent(QEvent.Close)
        
        with patch.object(event, 'ignore') as mock_ignore:
            self.window.closeEvent(event)
            mock_ignore.assert_called_once()
    
    def test_quit_application(self):
        """Test quit application functionality."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.skipTest("System tray not available on this system")
            
        self.window.create_system_tray()
        self.setup_tray_mock()
        
        with patch('sys.exit') as mock_exit:
            self.window.quit_application()
            
            # Verify cleanup was called
            self.window.stop_optimization.assert_called_once()
            self.window.stop_hotkeys.assert_called_once()
            self.window.save_settings.assert_called_once()
            mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
