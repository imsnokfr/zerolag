"""
Profile Switch Visual Feedback for ZeroLag

This module provides visual feedback for profile switching, including
on-screen notifications, status indicators, and user feedback.

Features:
- On-screen profile switch notifications
- Status bar integration
- Visual indicators for profile changes
- Customizable feedback appearance
- Integration with GUI components
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

try:
    from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
    from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
    from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QPen
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

from .profile_hotkeys import ProfileSwitchFeedback

logger = logging.getLogger(__name__)

class FeedbackStyle(Enum):
    """Visual feedback styles."""
    NOTIFICATION = "notification"
    STATUS_BAR = "status_bar"
    OVERLAY = "overlay"
    TOAST = "toast"

@dataclass
class FeedbackConfig:
    """Configuration for visual feedback."""
    style: FeedbackStyle = FeedbackStyle.NOTIFICATION
    duration: float = 2.0  # seconds
    position: str = "top_right"  # "top_left", "top_right", "bottom_left", "bottom_right", "center"
    show_profile_name: bool = True
    show_switch_time: bool = True
    show_success_status: bool = True
    background_color: str = "#2b2b2b"
    text_color: str = "#ffffff"
    success_color: str = "#4caf50"
    error_color: str = "#f44336"
    border_radius: int = 8
    font_size: int = 12
    padding: int = 12
    margin: int = 20
    fade_in_duration: float = 0.3
    fade_out_duration: float = 0.5

class ProfileSwitchNotification(QWidget):
    """On-screen notification widget for profile switching."""
    
    def __init__(self, config: FeedbackConfig, parent=None):
        if not PYQT5_AVAILABLE:
            raise ImportError("PyQt5 is required for visual feedback")
        
        super().__init__(parent)
        self.config = config
        self.feedback = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide)
        
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """Set up the notification UI."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 80)
        
        # Main frame
        self.frame = QFrame()
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.background_color};
                border-radius: {self.config.border_radius}px;
                border: 1px solid #444444;
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)
        
        # Content layout
        content_layout = QVBoxLayout(self.frame)
        content_layout.setContentsMargins(self.config.padding, self.config.padding, 
                                        self.config.padding, self.config.padding)
        
        # Profile name label
        self.profile_label = QLabel()
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setStyleSheet(f"""
            QLabel {{
                color: {self.config.text_color};
                font-size: {self.config.font_size + 2}px;
                font-weight: bold;
            }}
        """)
        content_layout.addWidget(self.profile_label)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.config.text_color};
                font-size: {self.config.font_size}px;
            }}
        """)
        content_layout.addWidget(self.status_label)
        
        # Switch time label
        if self.config.show_switch_time:
            self.time_label = QLabel()
            self.time_label.setAlignment(Qt.AlignCenter)
            self.time_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.config.text_color};
                    font-size: {self.config.font_size - 2}px;
                    opacity: 0.7;
                }}
            """)
            content_layout.addWidget(self.time_label)
        else:
            self.time_label = None
    
    def setup_animation(self):
        """Set up fade in/out animations."""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(int(self.config.fade_in_duration * 1000))
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def show_feedback(self, feedback: ProfileSwitchFeedback):
        """Show profile switch feedback."""
        self.feedback = feedback
        
        # Update labels
        if self.config.show_profile_name:
            self.profile_label.setText(f"Profile: {feedback.profile_name}")
        else:
            self.profile_label.setText("Profile Switched")
        
        if self.config.show_success_status:
            if feedback.success:
                self.status_label.setText("✓ Success")
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.config.success_color};
                        font-size: {self.config.font_size}px;
                    }}
                """)
            else:
                self.status_label.setText("✗ Failed")
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.config.error_color};
                        font-size: {self.config.font_size}px;
                    }}
                """)
        else:
            self.status_label.setText("")
        
        if self.time_label and self.config.show_switch_time:
            self.time_label.setText(f"Switch time: {feedback.switch_time:.3f}s")
        
        # Position the notification
        self.position_notification()
        
        # Show with animation
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Auto-hide after duration
        self.timer.stop()
        self.timer.start(int(self.config.duration * 1000))
    
    def position_notification(self):
        """Position the notification based on config."""
        if not self.parent():
            return
        
        parent_rect = self.parent().geometry()
        notification_rect = self.geometry()
        
        if self.config.position == "top_left":
            x = parent_rect.x() + self.config.margin
            y = parent_rect.y() + self.config.margin
        elif self.config.position == "top_right":
            x = parent_rect.x() + parent_rect.width() - notification_rect.width() - self.config.margin
            y = parent_rect.y() + self.config.margin
        elif self.config.position == "bottom_left":
            x = parent_rect.x() + self.config.margin
            y = parent_rect.y() + parent_rect.height() - notification_rect.height() - self.config.margin
        elif self.config.position == "bottom_right":
            x = parent_rect.x() + parent_rect.width() - notification_rect.width() - self.config.margin
            y = parent_rect.y() + parent_rect.height() - notification_rect.height() - self.config.margin
        else:  # center
            x = parent_rect.x() + (parent_rect.width() - notification_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - notification_rect.height()) // 2
        
        self.move(x, y)
    
    def hide_notification(self):
        """Hide the notification with fade out animation."""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()

class ProfileFeedbackManager:
    """
    Manages visual feedback for profile switching.
    
    This class coordinates different types of visual feedback
    and integrates with the GUI system.
    """
    
    def __init__(self, config: Optional[FeedbackConfig] = None):
        self.config = config or FeedbackConfig()
        self.notification = None
        self.feedback_callbacks: List[Callable[[ProfileSwitchFeedback], None]] = []
        
        logger.info("ProfileFeedbackManager initialized")
    
    def setup_notification(self, parent_widget=None):
        """Set up the notification widget."""
        if not PYQT5_AVAILABLE:
            logger.warning("PyQt5 not available - visual feedback disabled")
            return False
        
        try:
            self.notification = ProfileSwitchNotification(self.config, parent_widget)
            logger.info("Profile switch notification widget created")
            return True
        except Exception as e:
            logger.error(f"Error setting up notification widget: {e}")
            return False
    
    def show_feedback(self, feedback: ProfileSwitchFeedback):
        """Show visual feedback for profile switching."""
        try:
            if self.notification:
                self.notification.show_feedback(feedback)
            
            # Notify callbacks
            for callback in self.feedback_callbacks:
                try:
                    callback(feedback)
                except Exception as e:
                    logger.error(f"Error in feedback callback: {e}")
            
            logger.debug(f"Showed feedback for profile switch: {feedback.profile_name}")
            
        except Exception as e:
            logger.error(f"Error showing feedback: {e}")
    
    def add_feedback_callback(self, callback: Callable[[ProfileSwitchFeedback], None]):
        """Add a feedback callback."""
        self.feedback_callbacks.append(callback)
        logger.info("Added profile switch feedback callback")
    
    def remove_feedback_callback(self, callback: Callable[[ProfileSwitchFeedback], None]):
        """Remove a feedback callback."""
        if callback in self.feedback_callbacks:
            self.feedback_callbacks.remove(callback)
            logger.info("Removed profile switch feedback callback")
    
    def update_config(self, new_config: FeedbackConfig):
        """Update feedback configuration."""
        self.config = new_config
        if self.notification:
            self.notification.config = new_config
        logger.info("Updated profile feedback configuration")
    
    def hide_notification(self):
        """Hide the current notification."""
        if self.notification:
            self.notification.hide_notification()

class ConsoleFeedback:
    """Simple console-based feedback for profile switching."""
    
    def __init__(self):
        self.enabled = True
        logger.info("Console feedback initialized")
    
    def show_feedback(self, feedback: ProfileSwitchFeedback):
        """Show console feedback for profile switching."""
        if not self.enabled:
            return
        
        try:
            status_symbol = "✓" if feedback.success else "✗"
            status_color = "\033[92m" if feedback.success else "\033[91m"  # Green or Red
            reset_color = "\033[0m"
            
            print(f"{status_color}{status_symbol} Profile Switch{reset_color}: {feedback.profile_name}")
            if feedback.message:
                print(f"  Message: {feedback.message}")
            if feedback.switch_time > 0:
                print(f"  Switch time: {feedback.switch_time:.3f}s")
            print()  # Empty line for separation
            
        except Exception as e:
            logger.error(f"Error showing console feedback: {e}")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable console feedback."""
        self.enabled = enabled
        logger.info(f"Console feedback {'enabled' if enabled else 'disabled'}")

# Global feedback manager instance
_feedback_manager = None

def get_feedback_manager() -> ProfileFeedbackManager:
    """Get the global feedback manager instance."""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = ProfileFeedbackManager()
    return _feedback_manager

def setup_profile_feedback(parent_widget=None, config: Optional[FeedbackConfig] = None) -> bool:
    """Set up profile feedback system."""
    manager = get_feedback_manager()
    if config:
        manager.update_config(config)
    return manager.setup_notification(parent_widget)

def show_profile_feedback(feedback: ProfileSwitchFeedback):
    """Show profile switch feedback."""
    manager = get_feedback_manager()
    manager.show_feedback(feedback)
