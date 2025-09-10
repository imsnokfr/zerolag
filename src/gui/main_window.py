"""
Main GUI window for ZeroLag application using PyQt5.

This module provides the main application window with controls for:
- DPI adjustment (400-26000)
- Polling rate settings (125-8000Hz)
- Profile management
- Real-time performance monitoring
- System tray integration
"""

import sys
import time
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSlider, QPushButton, QComboBox, QGroupBox, QProgressBar,
    QTextEdit, QTabWidget, QSpinBox, QCheckBox, QFrame, QSplitter,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

from src.core.input.input_handler import InputHandler
from src.core.input.mouse_handler import GamingMouseHandler
from src.core.input.keyboard_handler import GamingKeyboardHandler
from src.core.profiles import ProfileManager, GamingModePresets, ProfileExporter
from src.core.hotkeys import (
    HotkeyManager, HotkeyConfigManager, HotkeyPresetManager,
    EmergencyHotkeyManager, EmergencyIntegration
)
from src.core.community import (
    ProfileSharingManager, GitHubProfileRepository, ProfileRepositoryConfig,
    ProfileLibraryManager, ProfileSearchFilter, ProfileCategory, ProfileDifficulty,
    ProfileValidator, CompatibilityChecker, SortOrder
)
from src.core.profiles import Profile
from pathlib import Path


class PerformanceMonitor(QThread):
    """Thread for monitoring performance metrics in real-time."""
    
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, input_handler: InputHandler, mouse_handler: GamingMouseHandler, keyboard_handler: GamingKeyboardHandler):
        super().__init__()
        self.input_handler = input_handler
        self.mouse_handler = mouse_handler
        self.keyboard_handler = keyboard_handler
        self.running = False
        
    def run(self):
        """Main monitoring loop."""
        self.running = True
        while self.running:
            try:
                # Collect performance stats
                input_stats = self.input_handler.get_performance_stats()
                mouse_stats = self.mouse_handler.get_performance_stats()
                keyboard_stats = self.keyboard_handler.get_keyboard_stats()
                
                # Combine stats
                combined_stats = {
                    'input': input_stats,
                    'mouse': mouse_stats,
                    'keyboard': keyboard_stats,
                    'timestamp': time.time()
                }
                
                self.stats_updated.emit(combined_stats)
                self.msleep(100)  # Update every 100ms
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                self.msleep(1000)
    
    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        self.wait()


class ZeroLagMainWindow(QMainWindow):
    """Main application window for ZeroLag."""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('ZeroLag', 'Settings')
        self.input_handler = None
        self.mouse_handler = None
        self.keyboard_handler = None
        self.performance_monitor = None
        
        # Initialize profile management
        self.profile_manager = ProfileManager()
        self.profile_exporter = ProfileExporter()
        
        # Initialize hotkey management
        self.hotkey_manager = None
        self.hotkey_config_manager = HotkeyConfigManager()
        self.hotkey_preset_manager = HotkeyPresetManager()
        self.emergency_hotkey_manager = None
        self.emergency_integration = None
        
        # Initialize community profile sharing
        self.profile_sharing_manager = None
        self.profile_library_manager = None
        self.profile_validator = ProfileValidator()
        self.compatibility_checker = CompatibilityChecker()
        
        self.init_ui()
        self.init_input_handlers()
        self.init_hotkey_handlers()
        self.load_settings()
        self.refresh_profile_list()
        self.refresh_hotkey_list()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ZeroLag - Gaming Input Optimizer")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Set modern dark theme with gaming aesthetics
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1a1a1a, stop:1 #0d0d0d);
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                color: #ffffff;
                border: 2px solid #333333;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2a2a2a, stop:1 #1f1f1f);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1a1a1a, stop:1 #0d0d0d);
                color: #00d4ff;
                font-weight: 700;
                font-size: 13px;
            }
            
            /* Labels */
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #333333, stop:0.5 #444444, stop:1 #333333);
                border-radius: 3px;
                margin: 4px 0;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00d4ff, stop:1 #0099cc);
                border: 2px solid #ffffff;
                width: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #33e0ff, stop:1 #00aadd);
                border: 2px solid #ffffff;
            }
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0099cc, stop:1 #006699);
            }
            
            /* Buttons */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #404040, stop:1 #2a2a2a);
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                color: #ffffff;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #505050, stop:1 #3a3a3a);
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 1px solid #444444;
            }
            
            /* Success Button */
            QPushButton[class="success"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #388E3C);
                border: 1px solid #66BB6A;
                color: #ffffff;
            }
            QPushButton[class="success"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #66BB6A, stop:1 #4CAF50);
            }
            
            /* Danger Button */
            QPushButton[class="danger"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f44336, stop:1 #d32f2f);
                border: 1px solid #ef5350;
                color: #ffffff;
            }
            QPushButton[class="danger"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ef5350, stop:1 #f44336);
            }
            
            /* Primary Button */
            QPushButton[class="primary"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2196F3, stop:1 #1976D2);
                border: 1px solid #42A5F5;
                color: #ffffff;
            }
            QPushButton[class="primary"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            
            /* ComboBox */
            QComboBox {
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #404040, stop:1 #2a2a2a);
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #666666;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 6px;
                color: #e0e0e0;
                selection-background-color: #404040;
            }
            
            /* SpinBox */
            QSpinBox {
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #404040, stop:1 #2a2a2a);
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
            }
            QSpinBox:hover {
                border: 1px solid #666666;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #404040;
                border: 1px solid #555555;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #505050;
            }
            
            /* TextEdit */
            QTextEdit {
                border: 1px solid #555555;
                border-radius: 6px;
                background: #1a1a1a;
                color: #e0e0e0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 2px solid #00d4ff;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 6px;
                text-align: center;
                background: #2a2a2a;
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00d4ff, stop:1 #0099cc);
                border-radius: 5px;
            }
            
            /* CheckBox */
            QCheckBox {
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555555;
                border-radius: 3px;
                background: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00d4ff, stop:1 #0099cc);
                border: 2px solid #00d4ff;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #666666;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #555555;
                border-radius: 6px;
                background: #1a1a1a;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #404040, stop:1 #2a2a2a);
                border: 1px solid #555555;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                color: #e0e0e0;
                font-weight: 600;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00d4ff, stop:1 #0099cc);
                color: #ffffff;
                border: 1px solid #00d4ff;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #505050, stop:1 #3a3a3a);
            }
            
            /* Status Bar */
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2a2a2a, stop:1 #1a1a1a);
                border-top: 1px solid #555555;
                color: #e0e0e0;
                font-size: 12px;
                font-weight: 500;
            }
            
            /* Splitter */
            QSplitter::handle {
                background: #555555;
                width: 2px;
            }
            QSplitter::handle:hover {
                background: #666666;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add title header
        title_layout = QHBoxLayout()
        title_label = QLabel("ZEROLAG")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 900;
            color: #00d4ff;
            margin: 10px 0;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        subtitle_label = QLabel("Gaming Input Optimizer")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #888888;
            margin: 10px 0;
        """)
        title_layout.addWidget(subtitle_label)
        main_layout.addLayout(title_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #333333;
                background-color: #333333;
                border: none;
                height: 1px;
                margin: 5px 0;
            }
        """)
        main_layout.addWidget(separator)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        self.create_controls_panel(splitter)
        
        # Right panel - Monitoring and Logs
        self.create_monitoring_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Create status bar
        self.create_status_bar()
        
        # Create system tray
        self.create_system_tray()
        
    def create_controls_panel(self, parent):
        """Create the left panel with input controls."""
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # DPI Control Group
        dpi_group = QGroupBox("DPI Settings")
        dpi_layout = QVBoxLayout(dpi_group)
        
        # DPI Slider
        dpi_layout.addWidget(QLabel("DPI: 800"))
        self.dpi_slider = QSlider(Qt.Horizontal)
        self.dpi_slider.setMinimum(400)
        self.dpi_slider.setMaximum(26000)
        self.dpi_slider.setValue(800)
        self.dpi_slider.setTickPosition(QSlider.TicksBelow)
        self.dpi_slider.setTickInterval(2000)
        self.dpi_slider.valueChanged.connect(self.on_dpi_changed)
        dpi_layout.addWidget(self.dpi_slider)
        
        # DPI Value Display
        dpi_value_layout = QHBoxLayout()
        dpi_value_layout.addWidget(QLabel("Value:"))
        self.dpi_value_label = QLabel("800")
        self.dpi_value_label.setStyleSheet("font-weight: 700; color: #00d4ff; font-size: 14px;")
        dpi_value_layout.addWidget(self.dpi_value_label)
        dpi_value_layout.addStretch()
        dpi_layout.addLayout(dpi_value_layout)
        
        controls_layout.addWidget(dpi_group)
        
        # Polling Rate Control Group
        polling_group = QGroupBox("Polling Rate Settings")
        polling_layout = QVBoxLayout(polling_group)
        
        # Mouse Polling Rate
        mouse_polling_layout = QHBoxLayout()
        mouse_polling_layout.addWidget(QLabel("Mouse:"))
        self.mouse_polling_combo = QComboBox()
        self.mouse_polling_combo.addItems(["125Hz", "250Hz", "500Hz", "1000Hz", "2000Hz", "4000Hz", "8000Hz"])
        self.mouse_polling_combo.setCurrentText("1000Hz")
        self.mouse_polling_combo.currentTextChanged.connect(self.on_mouse_polling_changed)
        mouse_polling_layout.addWidget(self.mouse_polling_combo)
        mouse_polling_layout.addStretch()
        polling_layout.addLayout(mouse_polling_layout)
        
        # Keyboard Polling Rate
        keyboard_polling_layout = QHBoxLayout()
        keyboard_polling_layout.addWidget(QLabel("Keyboard:"))
        self.keyboard_polling_combo = QComboBox()
        self.keyboard_polling_combo.addItems(["125Hz", "250Hz", "500Hz", "1000Hz", "2000Hz", "4000Hz", "8000Hz"])
        self.keyboard_polling_combo.setCurrentText("1000Hz")
        self.keyboard_polling_combo.currentTextChanged.connect(self.on_keyboard_polling_changed)
        keyboard_polling_layout.addWidget(self.keyboard_polling_combo)
        keyboard_polling_layout.addStretch()
        polling_layout.addLayout(keyboard_polling_layout)
        
        controls_layout.addWidget(polling_group)
        
        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Smoothing
        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(QLabel("Smoothing:"))
        self.smoothing_checkbox = QCheckBox("Enable")
        self.smoothing_checkbox.setChecked(True)
        smoothing_layout.addWidget(self.smoothing_checkbox)
        smoothing_layout.addStretch()
        advanced_layout.addLayout(smoothing_layout)
        
        # Anti-ghosting
        antighost_layout = QHBoxLayout()
        antighost_layout.addWidget(QLabel("Anti-ghosting:"))
        self.antighost_checkbox = QCheckBox("Enable")
        self.antighost_checkbox.setChecked(True)
        antighost_layout.addWidget(self.antighost_checkbox)
        antighost_layout.addStretch()
        advanced_layout.addLayout(antighost_layout)
        
        # NKRO Mode
        nkro_layout = QHBoxLayout()
        nkro_layout.addWidget(QLabel("NKRO Mode:"))
        self.nkro_combo = QComboBox()
        self.nkro_combo.addItems(["Disabled", "Basic (6KRO)", "Full NKRO", "Gaming (20KRO)"])
        self.nkro_combo.setCurrentText("Gaming (20KRO)")
        self.nkro_combo.currentTextChanged.connect(self.on_nkro_changed)
        nkro_layout.addWidget(self.nkro_combo)
        nkro_layout.addStretch()
        advanced_layout.addLayout(nkro_layout)
        
        # Rapid Trigger
        rapid_trigger_layout = QHBoxLayout()
        rapid_trigger_layout.addWidget(QLabel("Rapid Trigger:"))
        self.rapid_trigger_checkbox = QCheckBox("Enable")
        self.rapid_trigger_checkbox.setChecked(False)
        self.rapid_trigger_checkbox.toggled.connect(self.on_rapid_trigger_changed)
        rapid_trigger_layout.addWidget(self.rapid_trigger_checkbox)
        rapid_trigger_layout.addStretch()
        advanced_layout.addLayout(rapid_trigger_layout)
        
        # Debounce Threshold
        debounce_layout = QHBoxLayout()
        debounce_layout.addWidget(QLabel("Debounce:"))
        self.debounce_slider = QSlider(Qt.Horizontal)
        self.debounce_slider.setMinimum(1)
        self.debounce_slider.setMaximum(100)
        self.debounce_slider.setValue(50)
        self.debounce_slider.setTickPosition(QSlider.TicksBelow)
        self.debounce_slider.setTickInterval(25)
        self.debounce_slider.valueChanged.connect(self.on_debounce_changed)
        debounce_layout.addWidget(self.debounce_slider)
        self.debounce_label = QLabel("50ms")
        self.debounce_label.setStyleSheet("font-weight: 700; color: #00d4ff; font-size: 14px;")
        debounce_layout.addWidget(self.debounce_label)
        advanced_layout.addLayout(debounce_layout)
        
        controls_layout.addWidget(advanced_group)
        
        # Profile Management Group
        profile_group = QGroupBox("Profile Management")
        profile_layout = QVBoxLayout(profile_group)
        
        # Profile Selection
        profile_select_layout = QHBoxLayout()
        profile_select_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Default", "FPS", "MOBA", "RTS", "Custom"])
        profile_select_layout.addWidget(self.profile_combo)
        profile_select_layout.addStretch()
        profile_layout.addLayout(profile_select_layout)
        
        # Gaming Mode Presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Gaming Mode:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["FPS", "MOBA", "RTS", "MMO", "Productivity", "Custom"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        profile_layout.addLayout(preset_layout)
        
        # Profile Buttons
        profile_buttons_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton("Save")
        self.load_profile_btn = QPushButton("Load")
        self.delete_profile_btn = QPushButton("Delete")
        profile_buttons_layout.addWidget(self.save_profile_btn)
        profile_buttons_layout.addWidget(self.load_profile_btn)
        profile_buttons_layout.addWidget(self.delete_profile_btn)
        profile_layout.addLayout(profile_buttons_layout)
        
        # Import/Export Buttons
        import_export_layout = QHBoxLayout()
        self.import_profile_btn = QPushButton("Import")
        self.export_profile_btn = QPushButton("Export")
        import_export_layout.addWidget(self.import_profile_btn)
        import_export_layout.addWidget(self.export_profile_btn)
        profile_layout.addLayout(import_export_layout)
        
        controls_layout.addWidget(profile_group)
        
        # Control Buttons
        control_buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Optimization")
        self.start_btn.setProperty("class", "success")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setProperty("class", "danger")
        control_buttons_layout.addWidget(self.start_btn)
        control_buttons_layout.addWidget(self.stop_btn)
        controls_layout.addLayout(control_buttons_layout)
        
        # Connect button signals
        self.start_btn.clicked.connect(self.start_optimization)
        self.stop_btn.clicked.connect(self.stop_optimization)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.import_profile_btn.clicked.connect(self.import_profile)
        self.export_profile_btn.clicked.connect(self.export_profile)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        
        # Connect checkbox signals
        self.smoothing_checkbox.toggled.connect(self.on_smoothing_changed)
        
        controls_layout.addStretch()
        parent.addWidget(controls_widget)
        
    def create_monitoring_panel(self, parent):
        """Create the right panel with monitoring and logs."""
        monitoring_widget = QWidget()
        monitoring_layout = QVBoxLayout(monitoring_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        monitoring_layout.addWidget(tab_widget)
        
        # Performance Tab
        self.create_performance_tab(tab_widget)
        
        # Logs Tab
        self.create_logs_tab(tab_widget)
        
        # Settings Tab
        self.create_settings_tab(tab_widget)
        
        # Hotkeys Tab
        self.create_hotkeys_tab(tab_widget)
        
        # Community Tab
        self.create_community_tab(tab_widget)
        
        parent.addWidget(monitoring_widget)
        
    def create_performance_tab(self, parent):
        """Create the performance monitoring tab."""
        performance_widget = QWidget()
        performance_layout = QVBoxLayout(performance_widget)
        
        # Performance Stats Group
        stats_group = QGroupBox("Real-time Performance")
        stats_layout = QGridLayout(stats_group)
        
        # CPU Usage
        stats_layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        stats_layout.addWidget(self.cpu_progress, 0, 1)
        
        # Memory Usage
        stats_layout.addWidget(QLabel("Memory:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        stats_layout.addWidget(self.memory_progress, 1, 1)
        
        # Latency
        stats_layout.addWidget(QLabel("Latency:"), 2, 0)
        self.latency_label = QLabel("0.0ms")
        self.latency_label.setStyleSheet("color: #00d4ff; font-weight: 700; font-size: 14px;")
        stats_layout.addWidget(self.latency_label, 2, 1)
        
        # Events/sec
        stats_layout.addWidget(QLabel("Events/sec:"), 3, 0)
        self.events_per_sec_label = QLabel("0")
        self.events_per_sec_label.setStyleSheet("color: #00d4ff; font-weight: 700; font-size: 14px;")
        stats_layout.addWidget(self.events_per_sec_label, 3, 1)
        
        performance_layout.addWidget(stats_group)
        
        # Input Stats Group
        input_stats_group = QGroupBox("Input Statistics")
        input_stats_layout = QVBoxLayout(input_stats_group)
        
        self.input_stats_text = QTextEdit()
        self.input_stats_text.setMaximumHeight(150)
        self.input_stats_text.setReadOnly(True)
        input_stats_layout.addWidget(self.input_stats_text)
        
        performance_layout.addWidget(input_stats_group)
        
        # Mouse Stats Group
        mouse_stats_group = QGroupBox("Mouse Statistics")
        mouse_stats_layout = QVBoxLayout(mouse_stats_group)
        
        self.mouse_stats_text = QTextEdit()
        self.mouse_stats_text.setMaximumHeight(150)
        self.mouse_stats_text.setReadOnly(True)
        mouse_stats_layout.addWidget(self.mouse_stats_text)
        
        performance_layout.addWidget(mouse_stats_group)
        
        # Keyboard Stats Group
        keyboard_stats_group = QGroupBox("Keyboard Statistics")
        keyboard_stats_layout = QVBoxLayout(keyboard_stats_group)
        
        self.keyboard_stats_text = QTextEdit()
        self.keyboard_stats_text.setMaximumHeight(150)
        self.keyboard_stats_text.setReadOnly(True)
        keyboard_stats_layout.addWidget(self.keyboard_stats_text)
        
        performance_layout.addWidget(keyboard_stats_group)
        
        parent.addTab(performance_widget, "Performance")
        
    def create_logs_tab(self, parent):
        """Create the logs tab."""
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        
        # Log Level Selection
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        
        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        log_level_layout.addWidget(self.clear_logs_btn)
        
        logs_layout.addLayout(log_level_layout)
        
        # Log Display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        
        parent.addTab(logs_widget, "Logs")
        
    def create_settings_tab(self, parent):
        """Create the settings tab."""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # General Settings Group
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        
        # Auto-start
        auto_start_layout = QHBoxLayout()
        self.auto_start_checkbox = QCheckBox("Start with Windows")
        self.auto_start_checkbox.setChecked(False)
        auto_start_layout.addWidget(self.auto_start_checkbox)
        auto_start_layout.addStretch()
        general_layout.addLayout(auto_start_layout)
        
        # Minimize to tray
        minimize_tray_layout = QHBoxLayout()
        self.minimize_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_tray_checkbox.setChecked(True)
        minimize_tray_layout.addWidget(self.minimize_tray_checkbox)
        minimize_tray_layout.addStretch()
        general_layout.addLayout(minimize_tray_layout)
        
        # Show notifications
        notifications_layout = QHBoxLayout()
        self.notifications_checkbox = QCheckBox("Show notifications")
        self.notifications_checkbox.setChecked(True)
        notifications_layout.addWidget(self.notifications_checkbox)
        notifications_layout.addStretch()
        general_layout.addLayout(notifications_layout)
        
        settings_layout.addWidget(general_group)
        
        # Performance Settings Group
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QVBoxLayout(perf_group)
        
        # Queue Size
        queue_size_layout = QHBoxLayout()
        queue_size_layout.addWidget(QLabel("Event Queue Size:"))
        self.queue_size_spinbox = QSpinBox()
        self.queue_size_spinbox.setRange(1000, 10000)
        self.queue_size_spinbox.setValue(5000)
        queue_size_layout.addWidget(self.queue_size_spinbox)
        queue_size_layout.addStretch()
        perf_layout.addLayout(queue_size_layout)
        
        # Update Frequency
        update_freq_layout = QHBoxLayout()
        update_freq_layout.addWidget(QLabel("Update Frequency (ms):"))
        self.update_freq_spinbox = QSpinBox()
        self.update_freq_spinbox.setRange(50, 1000)
        self.update_freq_spinbox.setValue(100)
        update_freq_layout.addWidget(self.update_freq_spinbox)
        update_freq_layout.addStretch()
        perf_layout.addLayout(update_freq_layout)
        
        settings_layout.addWidget(perf_group)
        
        # Save/Load Settings
        settings_buttons_layout = QHBoxLayout()
        self.save_settings_btn = QPushButton("Save Settings")
        self.load_settings_btn = QPushButton("Load Settings")
        self.reset_settings_btn = QPushButton("Reset to Defaults")
        settings_buttons_layout.addWidget(self.save_settings_btn)
        settings_buttons_layout.addWidget(self.load_settings_btn)
        settings_buttons_layout.addWidget(self.reset_settings_btn)
        settings_layout.addLayout(settings_buttons_layout)
        
        # Connect settings signals
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.load_settings_btn.clicked.connect(self.load_settings)
        self.reset_settings_btn.clicked.connect(self.reset_settings)
        
        settings_layout.addStretch()
        parent.addTab(settings_widget, "Settings")
        
    def create_hotkeys_tab(self, parent):
        """Create the hotkeys configuration tab."""
        hotkeys_widget = QWidget()
        hotkeys_layout = QVBoxLayout(hotkeys_widget)
        
        # Hotkey Profile Management Group
        profile_group = QGroupBox("Hotkey Profiles")
        profile_layout = QVBoxLayout(profile_group)
        
        # Profile Selection
        profile_select_layout = QHBoxLayout()
        profile_select_layout.addWidget(QLabel("Active Profile:"))
        self.hotkey_profile_combo = QComboBox()
        self.hotkey_profile_combo.addItems(["Default", "FPS", "MOBA", "RTS", "Custom"])
        self.hotkey_profile_combo.currentTextChanged.connect(self.on_hotkey_profile_changed)
        profile_select_layout.addWidget(self.hotkey_profile_combo)
        profile_select_layout.addStretch()
        
        # Profile Management Buttons
        self.create_hotkey_profile_btn = QPushButton("New Profile")
        self.delete_hotkey_profile_btn = QPushButton("Delete Profile")
        profile_select_layout.addWidget(self.create_hotkey_profile_btn)
        profile_select_layout.addWidget(self.delete_hotkey_profile_btn)
        profile_layout.addLayout(profile_select_layout)
        
        # Preset Selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Apply Preset:"))
        self.hotkey_preset_combo = QComboBox()
        self.hotkey_preset_combo.addItems(["FPS", "MOBA", "RTS", "MMO", "Productivity", "Custom"])
        self.hotkey_preset_combo.currentTextChanged.connect(self.on_hotkey_preset_changed)
        preset_layout.addWidget(self.hotkey_preset_combo)
        preset_layout.addStretch()
        profile_layout.addLayout(preset_layout)
        
        hotkeys_layout.addWidget(profile_group)
        
        # Hotkey Bindings Group
        bindings_group = QGroupBox("Hotkey Bindings")
        bindings_layout = QVBoxLayout(bindings_group)
        
        # Add New Hotkey
        add_hotkey_layout = QHBoxLayout()
        add_hotkey_layout.addWidget(QLabel("Add Hotkey:"))
        
        # Modifier selection
        self.modifier_combo = QComboBox()
        self.modifier_combo.addItems(["None", "Ctrl", "Alt", "Shift", "Ctrl+Alt", "Ctrl+Shift", "Alt+Shift", "Ctrl+Alt+Shift"])
        add_hotkey_layout.addWidget(self.modifier_combo)
        
        # Key selection
        self.key_combo = QComboBox()
        self.key_combo.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
                                "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
                                "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
                                "A", "S", "D", "F", "G", "H", "J", "K", "L",
                                "Z", "X", "C", "V", "B", "N", "M",
                                "Space", "Enter", "Tab", "Esc", "Delete", "Backspace"])
        add_hotkey_layout.addWidget(self.key_combo)
        
        # Action selection
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "Profile Switch", "DPI Increase", "DPI Decrease", "DPI Reset",
            "Polling Rate Up", "Polling Rate Down", "Toggle Smoothing",
            "Toggle NKRO", "Toggle Rapid Trigger", "Emergency Stop",
            "Emergency Reset", "Disable All", "Toggle Optimization"
        ])
        add_hotkey_layout.addWidget(self.action_combo)
        
        self.add_hotkey_btn = QPushButton("Add")
        self.add_hotkey_btn.clicked.connect(self.add_hotkey)
        add_hotkey_layout.addWidget(self.add_hotkey_btn)
        
        bindings_layout.addLayout(add_hotkey_layout)
        
        # Hotkey List
        self.hotkey_list = QTextEdit()
        self.hotkey_list.setMaximumHeight(200)
        self.hotkey_list.setReadOnly(True)
        bindings_layout.addWidget(self.hotkey_list)
        
        # Hotkey Management Buttons
        hotkey_buttons_layout = QHBoxLayout()
        self.remove_hotkey_btn = QPushButton("Remove Selected")
        self.clear_hotkeys_btn = QPushButton("Clear All")
        self.test_hotkey_btn = QPushButton("Test Hotkey")
        hotkey_buttons_layout.addWidget(self.remove_hotkey_btn)
        hotkey_buttons_layout.addWidget(self.clear_hotkeys_btn)
        hotkey_buttons_layout.addWidget(self.test_hotkey_btn)
        hotkey_buttons_layout.addStretch()
        bindings_layout.addLayout(hotkey_buttons_layout)
        
        hotkeys_layout.addWidget(bindings_group)
        
        # Emergency Hotkeys Group
        emergency_group = QGroupBox("Emergency Hotkeys")
        emergency_layout = QVBoxLayout(emergency_group)
        
        # Emergency Stop
        emergency_stop_layout = QHBoxLayout()
        emergency_stop_layout.addWidget(QLabel("Emergency Stop:"))
        self.emergency_stop_combo = QComboBox()
        self.emergency_stop_combo.addItems(["Ctrl+Alt+Esc", "Ctrl+Shift+Esc", "Alt+F4", "Ctrl+Alt+Q"])
        emergency_stop_layout.addWidget(self.emergency_stop_combo)
        emergency_stop_layout.addStretch()
        emergency_layout.addLayout(emergency_stop_layout)
        
        # Emergency Reset
        emergency_reset_layout = QHBoxLayout()
        emergency_reset_layout.addWidget(QLabel("Emergency Reset:"))
        self.emergency_reset_combo = QComboBox()
        self.emergency_reset_combo.addItems(["Ctrl+Alt+R", "Ctrl+Shift+R", "Alt+R", "Ctrl+Alt+Z"])
        emergency_reset_layout.addWidget(self.emergency_reset_combo)
        emergency_reset_layout.addStretch()
        emergency_layout.addLayout(emergency_reset_layout)
        
        # Disable All
        disable_all_layout = QHBoxLayout()
        disable_all_layout.addWidget(QLabel("Disable All:"))
        self.disable_all_combo = QComboBox()
        self.disable_all_combo.addItems(["Ctrl+Alt+D", "Ctrl+Shift+D", "Alt+D", "Ctrl+Alt+X"])
        disable_all_layout.addWidget(self.disable_all_combo)
        disable_all_layout.addStretch()
        emergency_layout.addLayout(disable_all_layout)
        
        # Emergency Status
        self.emergency_status_label = QLabel("Status: Ready")
        self.emergency_status_label.setStyleSheet("color: #00d4ff; font-weight: 700; font-size: 14px;")
        emergency_layout.addWidget(self.emergency_status_label)
        
        # Emergency Test Buttons
        emergency_test_layout = QHBoxLayout()
        self.test_emergency_stop_btn = QPushButton("Test Emergency Stop")
        self.test_emergency_stop_btn.setProperty("class", "danger")
        self.test_emergency_stop_btn.clicked.connect(self.test_emergency_stop)
        emergency_test_layout.addWidget(self.test_emergency_stop_btn)
        
        self.test_emergency_reset_btn = QPushButton("Test Emergency Reset")
        self.test_emergency_reset_btn.setProperty("class", "primary")
        self.test_emergency_reset_btn.clicked.connect(self.test_emergency_reset)
        emergency_test_layout.addWidget(self.test_emergency_reset_btn)
        
        self.test_emergency_disable_btn = QPushButton("Test Disable All")
        self.test_emergency_disable_btn.setProperty("class", "danger")
        self.test_emergency_disable_btn.clicked.connect(self.test_emergency_disable)
        emergency_test_layout.addWidget(self.test_emergency_disable_btn)
        
        emergency_layout.addLayout(emergency_test_layout)
        
        hotkeys_layout.addWidget(emergency_group)
        
        # Hotkey Control Buttons
        control_buttons_layout = QHBoxLayout()
        self.start_hotkeys_btn = QPushButton("Start Hotkeys")
        self.start_hotkeys_btn.setProperty("class", "success")
        self.stop_hotkeys_btn = QPushButton("Stop Hotkeys")
        self.stop_hotkeys_btn.setEnabled(False)
        self.stop_hotkeys_btn.setProperty("class", "danger")
        control_buttons_layout.addWidget(self.start_hotkeys_btn)
        control_buttons_layout.addWidget(self.stop_hotkeys_btn)
        control_buttons_layout.addStretch()
        hotkeys_layout.addLayout(control_buttons_layout)
        
        # Connect hotkey signals
        self.start_hotkeys_btn.clicked.connect(self.start_hotkeys)
        self.stop_hotkeys_btn.clicked.connect(self.stop_hotkeys)
        self.create_hotkey_profile_btn.clicked.connect(self.create_hotkey_profile)
        self.delete_hotkey_profile_btn.clicked.connect(self.delete_hotkey_profile)
        self.remove_hotkey_btn.clicked.connect(self.remove_hotkey)
        self.clear_hotkeys_btn.clicked.connect(self.clear_hotkeys)
        self.test_hotkey_btn.clicked.connect(self.test_hotkey)
        
        hotkeys_layout.addStretch()
        parent.addTab(hotkeys_widget, "Hotkeys")
    
    def create_community_tab(self, parent):
        """Create the community profile sharing tab."""
        community_widget = QWidget()
        community_layout = QVBoxLayout(community_widget)
        
        # Community Profile Library Group
        library_group = QGroupBox("Community Profile Library")
        library_layout = QVBoxLayout(library_group)
        
        # Search and Filter Controls
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.community_search_edit = QTextEdit()
        self.community_search_edit.setMaximumHeight(30)
        self.community_search_edit.setPlaceholderText("Search profiles by name, author, or tags...")
        search_layout.addWidget(self.community_search_edit)
        
        self.search_profiles_btn = QPushButton("Search")
        self.search_profiles_btn.clicked.connect(self.search_community_profiles)
        search_layout.addWidget(self.search_profiles_btn)
        library_layout.addLayout(search_layout)
        
        # Filter Controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItems(["All", "FPS", "MOBA", "RTS", "MMO", "Productivity", "Custom", "Experimental"])
        filter_layout.addWidget(self.category_filter_combo)
        
        filter_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_filter_combo = QComboBox()
        self.difficulty_filter_combo.addItems(["All", "Beginner", "Intermediate", "Advanced", "Expert"])
        filter_layout.addWidget(self.difficulty_filter_combo)
        
        filter_layout.addWidget(QLabel("Sort by:"))
        self.sort_filter_combo = QComboBox()
        self.sort_filter_combo.addItems(["Newest", "Most Downloaded", "Highest Rated", "Alphabetical"])
        filter_layout.addWidget(self.sort_filter_combo)
        
        filter_layout.addStretch()
        library_layout.addLayout(filter_layout)
        
        # Profile List
        self.community_profile_list = QTextEdit()
        self.community_profile_list.setReadOnly(True)
        self.community_profile_list.setMaximumHeight(200)
        self.community_profile_list.setPlaceholderText("No profiles found. Click 'Search' to find community profiles.")
        library_layout.addWidget(self.community_profile_list)
        
        # Profile Actions
        profile_actions_layout = QHBoxLayout()
        self.download_profile_btn = QPushButton("Download Selected")
        self.download_profile_btn.clicked.connect(self.download_community_profile)
        self.download_profile_btn.setEnabled(False)
        profile_actions_layout.addWidget(self.download_profile_btn)
        
        self.refresh_library_btn = QPushButton("Refresh Library")
        self.refresh_library_btn.clicked.connect(self.refresh_community_library)
        profile_actions_layout.addWidget(self.refresh_library_btn)
        
        self.sync_library_btn = QPushButton("Sync with Repository")
        self.sync_library_btn.clicked.connect(self.sync_community_library)
        profile_actions_layout.addWidget(self.sync_library_btn)
        
        profile_actions_layout.addStretch()
        library_layout.addLayout(profile_actions_layout)
        
        community_layout.addWidget(library_group)
        
        # Upload Profile Group
        upload_group = QGroupBox("Upload Profile to Community")
        upload_layout = QVBoxLayout(upload_group)
        
        # Profile Selection for Upload
        upload_profile_layout = QHBoxLayout()
        upload_profile_layout.addWidget(QLabel("Select Profile to Upload:"))
        self.upload_profile_combo = QComboBox()
        self.upload_profile_combo.currentTextChanged.connect(self.on_upload_profile_changed)
        upload_profile_layout.addWidget(self.upload_profile_combo)
        upload_profile_layout.addStretch()
        upload_layout.addLayout(upload_profile_layout)
        
        # Upload Metadata
        metadata_layout = QGridLayout()
        metadata_layout.addWidget(QLabel("Profile Name:"), 0, 0)
        self.upload_name_edit = QTextEdit()
        self.upload_name_edit.setMaximumHeight(30)
        self.upload_name_edit.setPlaceholderText("Enter a descriptive name for your profile...")
        metadata_layout.addWidget(self.upload_name_edit, 0, 1)
        
        metadata_layout.addWidget(QLabel("Description:"), 1, 0)
        self.upload_description_edit = QTextEdit()
        self.upload_description_edit.setMaximumHeight(60)
        self.upload_description_edit.setPlaceholderText("Describe your profile settings and what games it's optimized for...")
        metadata_layout.addWidget(self.upload_description_edit, 1, 1)
        
        metadata_layout.addWidget(QLabel("Category:"), 2, 0)
        self.upload_category_combo = QComboBox()
        self.upload_category_combo.addItems(["FPS", "MOBA", "RTS", "MMO", "Productivity", "Custom", "Experimental"])
        metadata_layout.addWidget(self.upload_category_combo, 2, 1)
        
        metadata_layout.addWidget(QLabel("Difficulty:"), 3, 0)
        self.upload_difficulty_combo = QComboBox()
        self.upload_difficulty_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        metadata_layout.addWidget(self.upload_difficulty_combo, 3, 1)
        
        metadata_layout.addWidget(QLabel("Tags (comma-separated):"), 4, 0)
        self.upload_tags_edit = QTextEdit()
        self.upload_tags_edit.setMaximumHeight(30)
        self.upload_tags_edit.setPlaceholderText("e.g., competitive, aim, low-sens, cs2")
        metadata_layout.addWidget(self.upload_tags_edit, 4, 1)
        
        upload_layout.addLayout(metadata_layout)
        
        # Upload Actions
        upload_actions_layout = QHBoxLayout()
        self.upload_profile_btn = QPushButton("Upload Profile")
        self.upload_profile_btn.clicked.connect(self.upload_community_profile)
        self.upload_profile_btn.setEnabled(False)
        upload_actions_layout.addWidget(self.upload_profile_btn)
        
        self.validate_profile_btn = QPushButton("Validate Profile")
        self.validate_profile_btn.clicked.connect(self.validate_upload_profile)
        upload_actions_layout.addWidget(self.validate_profile_btn)
        
        upload_actions_layout.addStretch()
        upload_layout.addLayout(upload_actions_layout)
        
        community_layout.addWidget(upload_group)
        
        # Community Status
        status_layout = QHBoxLayout()
        self.community_status_label = QLabel("Status: Ready")
        self.community_status_label.setStyleSheet("color: #00d4ff; font-weight: 700; font-size: 14px;")
        status_layout.addWidget(self.community_status_label)
        status_layout.addStretch()
        community_layout.addLayout(status_layout)
        
        community_layout.addStretch()
        parent.addTab(community_widget, "Community")
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Performance indicator
        self.performance_indicator = QLabel("●")
        self.performance_indicator.setStyleSheet("color: #ff4444; font-weight: 700; font-size: 16px;")
        self.status_bar.addPermanentWidget(self.performance_indicator)
        
    def create_system_tray(self):
        """Create the system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.log_message("System tray not available on this system", "WARNING")
            return
            
        # Create tray icon with custom icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())
        self.tray_icon.setToolTip("ZeroLag - Gaming Input Optimizer")
        
        # Create comprehensive tray menu
        self.tray_menu = QMenu()
        self.create_tray_menu()
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
        # Start tray update timer
        self.tray_update_timer = QTimer()
        self.tray_update_timer.timeout.connect(self.update_tray_status)
        self.tray_update_timer.start(5000)  # Update every 5 seconds
        
        self.log_message("System tray initialized successfully")
        
    def create_tray_icon(self):
        """Create a custom tray icon with status indicator."""
        # For now, use a standard icon - in production, this would be a custom icon
        # that changes based on status (active/inactive, profile, etc.)
        return self.style().standardIcon(self.style().SP_ComputerIcon)
        
    def create_tray_menu(self):
        """Create the comprehensive system tray menu."""
        # Clear existing menu
        self.tray_menu.clear()
        
        # Status section
        status_action = QAction("ZeroLag - Gaming Input Optimizer", self)
        status_action.setEnabled(False)
        self.tray_menu.addAction(status_action)
        
        # Current profile info
        current_profile = self.profile_combo.currentText()
        profile_action = QAction(f"Profile: {current_profile}", self)
        profile_action.setEnabled(False)
        self.tray_menu.addAction(profile_action)
        
        # Current DPI info
        current_dpi = self.dpi_slider.value()
        dpi_action = QAction(f"DPI: {current_dpi}", self)
        dpi_action.setEnabled(False)
        self.tray_menu.addAction(dpi_action)
        
        self.tray_menu.addSeparator()
        
        # Quick profile switching
        profile_menu = self.tray_menu.addMenu("Switch Profile")
        for i in range(self.profile_combo.count()):
            profile_name = self.profile_combo.itemText(i)
            profile_action = QAction(profile_name, self)
            profile_action.triggered.connect(lambda checked, name=profile_name: self.switch_profile_from_tray(name))
            profile_menu.addAction(profile_action)
        
        # Quick DPI controls
        dpi_menu = self.tray_menu.addMenu("DPI Control")
        
        # DPI presets
        dpi_presets = [400, 800, 1600, 3200, 6400, 12800, 26000]
        for dpi in dpi_presets:
            dpi_action = QAction(f"Set to {dpi} DPI", self)
            dpi_action.triggered.connect(lambda checked, value=dpi: self.set_dpi_from_tray(value))
            dpi_menu.addAction(dpi_action)
        
        dpi_menu.addSeparator()
        
        # DPI adjustment
        increase_dpi_action = QAction("Increase DPI (+100)", self)
        increase_dpi_action.triggered.connect(self.increase_dpi_from_tray)
        dpi_menu.addAction(increase_dpi_action)
        
        decrease_dpi_action = QAction("Decrease DPI (-100)", self)
        decrease_dpi_action.triggered.connect(self.decrease_dpi_from_tray)
        dpi_menu.addAction(decrease_dpi_action)
        
        self.tray_menu.addSeparator()
        
        # Quick settings
        settings_menu = self.tray_menu.addMenu("Quick Settings")
        
        # Toggle optimization
        self.toggle_optimization_action = QAction("Start Optimization", self)
        self.toggle_optimization_action.triggered.connect(self.toggle_optimization_from_tray)
        settings_menu.addAction(self.toggle_optimization_action)
        
        # Toggle hotkeys
        self.toggle_hotkeys_action = QAction("Start Hotkeys", self)
        self.toggle_hotkeys_action.triggered.connect(self.toggle_hotkeys_from_tray)
        settings_menu.addAction(self.toggle_hotkeys_action)
        
        settings_menu.addSeparator()
        
        # Emergency controls
        emergency_stop_action = QAction("Emergency Stop", self)
        emergency_stop_action.triggered.connect(self.emergency_stop_from_tray)
        settings_menu.addAction(emergency_stop_action)
        
        reset_action = QAction("Reset to Defaults", self)
        reset_action.triggered.connect(self.reset_from_tray)
        settings_menu.addAction(reset_action)
        
        self.tray_menu.addSeparator()
        
        # Window controls
        if self.isVisible():
            hide_action = QAction("Hide Window", self)
            hide_action.triggered.connect(self.hide)
            self.tray_menu.addAction(hide_action)
        else:
            show_action = QAction("Show Window", self)
            show_action.triggered.connect(self.show_window_from_tray)
            self.tray_menu.addAction(show_action)
        
        self.tray_menu.addSeparator()
        
        # Exit
        quit_action = QAction("Exit ZeroLag", self)
        quit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(quit_action)
        
    def update_tray_status(self):
        """Update the tray menu with current status."""
        if hasattr(self, 'tray_menu'):
            self.create_tray_menu()
            
    def switch_profile_from_tray(self, profile_name):
        """Switch profile from tray menu."""
        try:
            # Find and select the profile
            index = self.profile_combo.findText(profile_name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
                self.apply_profile()
                self.tray_icon.showMessage(
                    "Profile Changed",
                    f"Switched to profile: {profile_name}",
                    QSystemTrayIcon.Information,
                    2000
                )
                self.log_message(f"Profile switched to {profile_name} from tray")
        except Exception as e:
            self.log_message(f"Error switching profile from tray: {e}", "ERROR")
            
    def set_dpi_from_tray(self, dpi_value):
        """Set DPI from tray menu."""
        try:
            self.dpi_slider.setValue(dpi_value)
            self.apply_dpi_settings()
            self.tray_icon.showMessage(
                "DPI Changed",
                f"DPI set to: {dpi_value}",
                QSystemTrayIcon.Information,
                2000
            )
            self.log_message(f"DPI set to {dpi_value} from tray")
        except Exception as e:
            self.log_message(f"Error setting DPI from tray: {e}", "ERROR")
            
    def increase_dpi_from_tray(self):
        """Increase DPI by 100 from tray menu."""
        current_dpi = self.dpi_slider.value()
        new_dpi = min(current_dpi + 100, self.dpi_slider.maximum())
        self.set_dpi_from_tray(new_dpi)
        
    def decrease_dpi_from_tray(self):
        """Decrease DPI by 100 from tray menu."""
        current_dpi = self.dpi_slider.value()
        new_dpi = max(current_dpi - 100, self.dpi_slider.minimum())
        self.set_dpi_from_tray(new_dpi)
        
    def toggle_optimization_from_tray(self):
        """Toggle optimization from tray menu."""
        if self.optimization_running:
            self.stop_optimization()
            self.tray_icon.showMessage(
                "Optimization Stopped",
                "ZeroLag optimization has been stopped",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.start_optimization()
            self.tray_icon.showMessage(
                "Optimization Started",
                "ZeroLag optimization is now running",
                QSystemTrayIcon.Information,
                2000
            )
            
    def toggle_hotkeys_from_tray(self):
        """Toggle hotkeys from tray menu."""
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager.is_running():
            self.stop_hotkeys()
            self.tray_icon.showMessage(
                "Hotkeys Stopped",
                "Hotkeys have been stopped",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.start_hotkeys()
            self.tray_icon.showMessage(
                "Hotkeys Started",
                "Hotkeys are now active",
                QSystemTrayIcon.Information,
                2000
            )
            
    def emergency_stop_from_tray(self):
        """Emergency stop from tray menu."""
        try:
            self.stop_optimization()
            if hasattr(self, 'hotkey_manager'):
                self.stop_hotkeys()
            self.tray_icon.showMessage(
                "Emergency Stop",
                "All ZeroLag functions have been stopped",
                QSystemTrayIcon.Critical,
                3000
            )
            self.log_message("Emergency stop activated from tray")
        except Exception as e:
            self.log_message(f"Error during emergency stop from tray: {e}", "ERROR")
    
    def test_emergency_stop(self):
        """Test emergency stop functionality."""
        try:
            if self.emergency_hotkey_manager:
                from src.core.hotkeys.hotkey_detector import HotkeyEvent, HotkeyModifier
                
                # Create test event
                test_event = HotkeyEvent(
                    hotkey_id=999,
                    modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    virtual_key=46,  # Delete key
                    event_type="key_press",
                    timestamp=time.time()
                )
                
                result = self.emergency_hotkey_manager.handle_emergency_stop(test_event)
                
                if result.success:
                    self.emergency_status_label.setText("Status: Emergency Stop Active")
                    self.emergency_status_label.setStyleSheet("color: #ff4444; font-weight: 700; font-size: 14px;")
                    self.log_message("Emergency stop test successful")
                    QMessageBox.information(self, "Test Result", "Emergency stop test successful!")
                else:
                    self.log_message(f"Emergency stop test failed: {result.message}", "ERROR")
                    QMessageBox.warning(self, "Test Result", f"Emergency stop test failed: {result.message}")
            else:
                QMessageBox.warning(self, "Test Error", "Emergency hotkey manager not available")
        except Exception as e:
            self.log_message(f"Error during emergency stop test: {e}", "ERROR")
            QMessageBox.critical(self, "Test Error", f"Error during emergency stop test: {e}")
    
    def test_emergency_reset(self):
        """Test emergency reset functionality."""
        try:
            if self.emergency_hotkey_manager:
                from src.core.hotkeys.hotkey_detector import HotkeyEvent, HotkeyModifier
                
                # Create test event
                test_event = HotkeyEvent(
                    hotkey_id=998,
                    modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    virtual_key=82,  # R key
                    event_type="key_press",
                    timestamp=time.time()
                )
                
                result = self.emergency_hotkey_manager.handle_emergency_reset(test_event)
                
                if result.success:
                    self.emergency_status_label.setText("Status: Emergency Reset Active")
                    self.emergency_status_label.setStyleSheet("color: #ffaa00; font-weight: 700; font-size: 14px;")
                    self.log_message("Emergency reset test successful")
                    QMessageBox.information(self, "Test Result", "Emergency reset test successful!")
                else:
                    self.log_message(f"Emergency reset test failed: {result.message}", "ERROR")
                    QMessageBox.warning(self, "Test Result", f"Emergency reset test failed: {result.message}")
            else:
                QMessageBox.warning(self, "Test Error", "Emergency hotkey manager not available")
        except Exception as e:
            self.log_message(f"Error during emergency reset test: {e}", "ERROR")
            QMessageBox.critical(self, "Test Error", f"Error during emergency reset test: {e}")
    
    def test_emergency_disable(self):
        """Test emergency disable all functionality."""
        try:
            if self.emergency_hotkey_manager:
                from src.core.hotkeys.hotkey_detector import HotkeyEvent, HotkeyModifier
                
                # Create test event
                test_event = HotkeyEvent(
                    hotkey_id=997,
                    modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    virtual_key=68,  # D key
                    event_type="key_press",
                    timestamp=time.time()
                )
                
                result = self.emergency_hotkey_manager.handle_emergency_disable_all(test_event)
                
                if result.success:
                    self.emergency_status_label.setText("Status: All Optimizations Disabled")
                    self.emergency_status_label.setStyleSheet("color: #ff4444; font-weight: 700; font-size: 14px;")
                    self.log_message("Emergency disable all test successful")
                    QMessageBox.information(self, "Test Result", "Emergency disable all test successful!")
                else:
                    self.log_message(f"Emergency disable all test failed: {result.message}", "ERROR")
                    QMessageBox.warning(self, "Test Result", f"Emergency disable all test failed: {result.message}")
            else:
                QMessageBox.warning(self, "Test Error", "Emergency hotkey manager not available")
        except Exception as e:
            self.log_message(f"Error during emergency disable test: {e}", "ERROR")
            QMessageBox.critical(self, "Test Error", f"Error during emergency disable test: {e}")
            
    def reset_from_tray(self):
        """Reset to defaults from tray menu."""
        try:
            # Reset to default profile
            self.profile_combo.setCurrentIndex(0)
            self.apply_profile()
            
            # Reset DPI to default
            self.dpi_slider.setValue(1600)
            self.apply_dpi_settings()
            
            self.tray_icon.showMessage(
                "Reset Complete",
                "Settings have been reset to defaults",
                QSystemTrayIcon.Information,
                2000
            )
            self.log_message("Settings reset to defaults from tray")
        except Exception as e:
            self.log_message(f"Error resetting from tray: {e}", "ERROR")
            
    def update_tray_optimization_status(self):
        """Update tray menu optimization status."""
        if hasattr(self, 'toggle_optimization_action'):
            if self.optimization_running:
                self.toggle_optimization_action.setText("Stop Optimization")
            else:
                self.toggle_optimization_action.setText("Start Optimization")
                
    def update_tray_hotkey_status(self):
        """Update tray menu hotkey status."""
        if hasattr(self, 'toggle_hotkeys_action'):
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager.is_running():
                self.toggle_hotkeys_action.setText("Stop Hotkeys")
            else:
                self.toggle_hotkeys_action.setText("Start Hotkeys")
            
    def show_window_from_tray(self):
        """Show window from tray menu."""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def quit_application(self):
        """Quit the application completely."""
        try:
            self.stop_optimization()
            if hasattr(self, 'hotkey_manager'):
                self.stop_hotkeys()
            self.save_settings()
            self.close()
            sys.exit(0)
        except Exception as e:
            self.log_message(f"Error quitting application: {e}", "ERROR")
        
    def init_input_handlers(self):
        """Initialize the input handlers."""
        try:
            self.input_handler = InputHandler()
            self.mouse_handler = GamingMouseHandler(self.input_handler)
            self.keyboard_handler = GamingKeyboardHandler(self.input_handler)
            
            # Initialize performance monitor
            self.performance_monitor = PerformanceMonitor(
                self.input_handler, self.mouse_handler, self.keyboard_handler
            )
            self.performance_monitor.stats_updated.connect(self.update_performance_stats)
            
            self.log_message("Input handlers initialized successfully")
            
        except Exception as e:
            self.log_message(f"Error initializing input handlers: {e}", "ERROR")
            
    def init_hotkey_handlers(self):
        """Initialize the hotkey handlers."""
        try:
            # Initialize hotkey manager
            self.hotkey_manager = HotkeyManager()
            
            # Initialize emergency hotkey manager
            self.emergency_hotkey_manager = EmergencyHotkeyManager()
            
            # Initialize emergency integration
            self.emergency_integration = EmergencyIntegration(
                emergency_manager=self.emergency_hotkey_manager,
                input_handler=self.input_handler,
                mouse_handler=self.mouse_handler,
                keyboard_handler=self.keyboard_handler
            )
            
            self.log_message("Hotkey handlers initialized successfully")
            
        except Exception as e:
            self.log_message(f"Error initializing hotkey handlers: {e}", "ERROR")
        
        # Initialize community profile sharing
        try:
            self.init_community_sharing()
        except Exception as e:
            self.log_message(f"Error initializing community sharing: {e}", "ERROR")
            
    def load_settings(self):
        """Load settings from QSettings."""
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Load DPI setting
        dpi = self.settings.value("dpi", 800, type=int)
        self.dpi_slider.setValue(dpi)
        self.dpi_value_label.setText(str(dpi))
        
        # Load polling rates
        mouse_polling = self.settings.value("mouse_polling", "1000Hz")
        keyboard_polling = self.settings.value("keyboard_polling", "1000Hz")
        self.mouse_polling_combo.setCurrentText(mouse_polling)
        self.keyboard_polling_combo.setCurrentText(keyboard_polling)
        
        # Load advanced settings
        self.smoothing_checkbox.setChecked(self.settings.value("smoothing", True, type=bool))
        self.antighost_checkbox.setChecked(self.settings.value("antighost", True, type=bool))
        self.rapid_trigger_checkbox.setChecked(self.settings.value("rapid_trigger", False, type=bool))
        
        # Load general settings
        self.auto_start_checkbox.setChecked(self.settings.value("auto_start", False, type=bool))
        self.minimize_tray_checkbox.setChecked(self.settings.value("minimize_tray", True, type=bool))
        self.notifications_checkbox.setChecked(self.settings.value("notifications", True, type=bool))
        
        # Load performance settings
        self.queue_size_spinbox.setValue(self.settings.value("queue_size", 5000, type=int))
        self.update_freq_spinbox.setValue(self.settings.value("update_freq", 100, type=int))
        
    def save_settings(self):
        """Save current settings to QSettings."""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Save DPI setting
        self.settings.setValue("dpi", self.dpi_slider.value())
        
        # Save polling rates
        self.settings.setValue("mouse_polling", self.mouse_polling_combo.currentText())
        self.settings.setValue("keyboard_polling", self.keyboard_polling_combo.currentText())
        
        # Save advanced settings
        self.settings.setValue("smoothing", self.smoothing_checkbox.isChecked())
        self.settings.setValue("antighost", self.antighost_checkbox.isChecked())
        self.settings.setValue("rapid_trigger", self.rapid_trigger_checkbox.isChecked())
        
        # Save general settings
        self.settings.setValue("auto_start", self.auto_start_checkbox.isChecked())
        self.settings.setValue("minimize_tray", self.minimize_tray_checkbox.isChecked())
        self.settings.setValue("notifications", self.notifications_checkbox.isChecked())
        
        # Save performance settings
        self.settings.setValue("queue_size", self.queue_size_spinbox.value())
        self.settings.setValue("update_freq", self.update_freq_spinbox.value())
        
        self.log_message("Settings saved successfully")
        
    def reset_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self.load_settings()
            self.log_message("Settings reset to defaults")
            
    def on_dpi_changed(self, value):
        """Handle DPI slider value change."""
        self.dpi_value_label.setText(str(value))
        
        # Apply DPI setting to mouse handler
        if self.mouse_handler:
            success = self.mouse_handler.set_dpi(value)
            if success:
                self.log_message(f"DPI changed to {value}")
            else:
                self.log_message(f"Failed to set DPI to {value}", "ERROR")
        else:
            self.log_message(f"DPI changed to {value} (will apply when mouse handler starts)")
        
    def on_mouse_polling_changed(self, value):
        """Handle mouse polling rate change."""
        # Extract rate from text (e.g., "1000 Hz" -> 1000)
        try:
            rate = int(value.split()[0])
            if self.input_handler:
                success = self.input_handler.set_mouse_polling_rate(rate)
                if success:
                    self.log_message(f"Mouse polling rate changed to {rate} Hz")
                else:
                    self.log_message(f"Failed to set mouse polling rate to {rate} Hz", "ERROR")
            else:
                self.log_message(f"Mouse polling rate changed to {rate} Hz (will apply when input handler starts)")
        except (ValueError, IndexError):
            self.log_message(f"Invalid mouse polling rate: {value}", "ERROR")
        
    def on_keyboard_polling_changed(self, value):
        """Handle keyboard polling rate change."""
        # Extract rate from text (e.g., "1000 Hz" -> 1000)
        try:
            rate = int(value.split()[0])
            if self.input_handler:
                success = self.input_handler.set_keyboard_polling_rate(rate)
                if success:
                    self.log_message(f"Keyboard polling rate changed to {rate} Hz")
                else:
                    self.log_message(f"Failed to set keyboard polling rate to {rate} Hz", "ERROR")
            else:
                self.log_message(f"Keyboard polling rate changed to {rate} Hz (will apply when input handler starts)")
        except (ValueError, IndexError):
            self.log_message(f"Invalid keyboard polling rate: {value}", "ERROR")
        
    def on_smoothing_changed(self, enabled):
        """Handle smoothing checkbox change."""
        if self.mouse_handler:
            self.mouse_handler.set_movement_smoothing(enabled)
            self.log_message(f"Movement smoothing {'enabled' if enabled else 'disabled'}")
        else:
            self.log_message(f"Movement smoothing {'enabled' if enabled else 'disabled'} (will apply when mouse handler starts)")
    
    def on_nkro_changed(self, value):
        """Handle NKRO mode change."""
        if self.keyboard_handler:
            from src.core.input.keyboard_handler import NKROMode
            
            # Map GUI values to NKROMode enum
            mode_map = {
                "Disabled": NKROMode.DISABLED,
                "Basic (6KRO)": NKROMode.BASIC,
                "Full NKRO": NKROMode.FULL,
                "Gaming (20KRO)": NKROMode.GAMING
            }
            
            if value in mode_map:
                self.keyboard_handler.set_nkro_mode(mode_map[value])
                self.log_message(f"NKRO mode changed to {value}")
            else:
                self.log_message(f"Invalid NKRO mode: {value}", "ERROR")
        else:
            self.log_message(f"NKRO mode changed to {value} (will apply when keyboard handler starts)")
    
    def on_rapid_trigger_changed(self, enabled):
        """Handle rapid trigger checkbox change."""
        if self.keyboard_handler:
            from src.core.input.keyboard_handler import RapidTriggerMode
            
            mode = RapidTriggerMode.LINEAR if enabled else RapidTriggerMode.DISABLED
            self.keyboard_handler.set_rapid_trigger_mode(mode)
            self.log_message(f"Rapid trigger {'enabled' if enabled else 'disabled'}")
        else:
            self.log_message(f"Rapid trigger {'enabled' if enabled else 'disabled'} (will apply when keyboard handler starts)")
    
    def on_debounce_changed(self, value):
        """Handle debounce threshold change."""
        # Convert slider value (1-100) to milliseconds (1-100ms)
        debounce_ms = value
        debounce_seconds = debounce_ms / 1000.0
        
        self.debounce_label.setText(f"{debounce_ms}ms")
        
        if self.keyboard_handler:
            self.keyboard_handler.set_debounce_threshold(debounce_seconds)
            self.log_message(f"Debounce threshold changed to {debounce_ms}ms")
        else:
            self.log_message(f"Debounce threshold changed to {debounce_ms}ms (will apply when keyboard handler starts)")
        
    def start_optimization(self):
        """Start the input optimization."""
        try:
            if self.input_handler and not self.input_handler.is_running:
                self.input_handler.start()
                self.mouse_handler.start_tracking()
                self.keyboard_handler.start_tracking()
                self.performance_monitor.start()
                
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText("Optimization Active")
                self.performance_indicator.setStyleSheet("color: #00ff44; font-weight: 700; font-size: 16px;")
                self.optimization_running = True
                self.update_tray_optimization_status()
                
                self.log_message("Input optimization started")
                
        except Exception as e:
            self.log_message(f"Error starting optimization: {e}", "ERROR")
            
    def stop_optimization(self):
        """Stop the input optimization."""
        try:
            if self.input_handler and self.input_handler.is_running:
                self.performance_monitor.stop()
                self.input_handler.stop()
                
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.status_label.setText("Ready")
                self.performance_indicator.setStyleSheet("color: #ff4444; font-weight: 700; font-size: 16px;")
                self.optimization_running = False
                self.update_tray_optimization_status()
                
                self.log_message("Input optimization stopped")
                
        except Exception as e:
            self.log_message(f"Error stopping optimization: {e}", "ERROR")
            
    def update_performance_stats(self, stats):
        """Update performance statistics display."""
        try:
            # Update progress bars
            input_stats = stats.get('input', {})
            mouse_stats = stats.get('mouse', {})
            keyboard_stats = stats.get('keyboard', {})
            
            # CPU usage (simplified calculation)
            cpu_usage = min(100, input_stats.get('events_processed', 0) / 100)
            self.cpu_progress.setValue(int(cpu_usage))
            
            # Memory usage (simplified calculation)
            memory_usage = min(100, input_stats.get('events_dropped', 0) / 10)
            self.memory_progress.setValue(int(memory_usage))
            
            # Latency
            latency = input_stats.get('avg_processing_time', 0) * 1000
            self.latency_label.setText(f"{latency:.1f}ms")
            
            # Events per second
            events_per_sec = input_stats.get('events_per_second', 0)
            self.events_per_sec_label.setText(str(events_per_sec))
            
            # Update text displays
            self.input_stats_text.setText(self.format_stats(input_stats))
            self.mouse_stats_text.setText(self.format_stats(mouse_stats))
            self.keyboard_stats_text.setText(self.format_stats(keyboard_stats))
            
        except Exception as e:
            self.log_message(f"Error updating performance stats: {e}", "ERROR")
            
    def format_stats(self, stats):
        """Format statistics dictionary for display."""
        if not stats:
            return "No data available"
            
        formatted = []
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                formatted.append(f"{key}: {value}")
            elif isinstance(value, dict):
                formatted.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  {sub_key}: {sub_value}")
            else:
                formatted.append(f"{key}: {value}")
                
        return "\n".join(formatted)
        
    def log_message(self, message, level="INFO"):
        """Add a message to the logs."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        self.logs_text.append(log_entry)
        
        # Auto-scroll to bottom
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.End)
        self.logs_text.setTextCursor(cursor)
        
    def clear_logs(self):
        """Clear the logs display."""
        self.logs_text.clear()
        
    def save_profile(self):
        """Save current settings as a profile."""
        profile_name = self.profile_combo.currentText()
        
        # Create profile from current settings
        profile = self.create_profile_from_current_settings(profile_name)
        
        # Save profile
        success = self.profile_manager.save_profile(profile)
        if success:
            self.log_message(f"Profile '{profile_name}' saved successfully")
            self.refresh_profile_list()
        else:
            QMessageBox.warning(self, "Save Failed", f"Failed to save profile '{profile_name}'")
        
    def load_profile(self):
        """Load a profile."""
        profile_name = self.profile_combo.currentText()
        
        # Load profile
        profile = self.profile_manager.get_profile(profile_name)
        if profile:
            self.apply_profile_to_settings(profile)
            self.log_message(f"Profile '{profile_name}' loaded successfully")
        else:
            QMessageBox.warning(self, "Load Failed", f"Profile '{profile_name}' not found")
        
    def delete_profile(self):
        """Delete a profile."""
        profile_name = self.profile_combo.currentText()
        if profile_name != "Default":
            reply = QMessageBox.question(
                self, "Delete Profile",
                f"Are you sure you want to delete profile '{profile_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.profile_manager.delete_profile(profile_name)
                if success:
                    self.log_message(f"Profile '{profile_name}' deleted")
                    self.refresh_profile_list()
                else:
                    QMessageBox.warning(self, "Delete Failed", f"Failed to delete profile '{profile_name}'")
        else:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the default profile.")
    
    def create_profile_from_current_settings(self, name: str):
        """Create a profile from current GUI settings."""
        from src.core.profiles import Profile, GamingMode, DPISettings, PollingSettings, KeyboardSettings, SmoothingSettings, MacroSettings, PerformanceSettings, GUISettings, HotkeySettings, ProfileSettings
        
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = f"Profile created from current settings"
        
        # DPI settings
        dpi_value = self.dpi_slider.value()
        profile.settings.dpi = DPISettings(
            enabled=True,
            dpi_value=dpi_value,
            sensitivity_multiplier=1.0,
            smoothing_enabled=self.smoothing_checkbox.isChecked()
        )
        
        # Polling settings
        mouse_polling = int(self.mouse_polling_combo.currentText().replace("Hz", ""))
        keyboard_polling = int(self.keyboard_polling_combo.currentText().replace("Hz", ""))
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=mouse_polling,
            keyboard_polling_rate=keyboard_polling
        )
        
        # Keyboard settings
        nkro_enabled = self.nkro_combo.currentText() != "Disabled"
        rapid_trigger_enabled = self.rapid_trigger_checkbox.isChecked()
        debounce_time = self.debounce_slider.value()
        
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=nkro_enabled,
            rapid_trigger_enabled=rapid_trigger_enabled,
            debounce_delay=debounce_time,
            anti_ghosting_enabled=self.antighost_checkbox.isChecked()
        )
        
        # Smoothing settings
        profile.settings.smoothing = SmoothingSettings(
            enabled=self.smoothing_checkbox.isChecked(),
            algorithm="EMA",
            strength=0.5
        )
        
        return profile
    
    def apply_profile_to_settings(self, profile):
        """Apply profile settings to GUI controls."""
        # Apply DPI settings
        self.dpi_slider.setValue(profile.settings.dpi.dpi_value)
        self.dpi_value_label.setText(str(profile.settings.dpi.dpi_value))
        
        # Apply polling settings
        mouse_polling_text = f"{profile.settings.polling.mouse_polling_rate}Hz"
        keyboard_polling_text = f"{profile.settings.polling.keyboard_polling_rate}Hz"
        self.mouse_polling_combo.setCurrentText(mouse_polling_text)
        self.keyboard_polling_combo.setCurrentText(keyboard_polling_text)
        
        # Apply keyboard settings
        self.smoothing_checkbox.setChecked(profile.settings.smoothing.enabled)
        self.antighost_checkbox.setChecked(profile.settings.keyboard.anti_ghosting_enabled)
        self.rapid_trigger_checkbox.setChecked(profile.settings.keyboard.rapid_trigger_enabled)
        self.debounce_slider.setValue(int(profile.settings.keyboard.debounce_delay))
        self.debounce_label.setText(f"{int(profile.settings.keyboard.debounce_delay)}ms")
        
        # Update NKRO combo
        if profile.settings.keyboard.nkro_enabled:
            self.nkro_combo.setCurrentText("Gaming (20KRO)")
        else:
            self.nkro_combo.setCurrentText("Disabled")
    
    def refresh_profile_list(self):
        """Refresh the profile combo box with current profiles."""
        self.profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        if profiles:
            self.profile_combo.addItems(profiles)
        else:
            self.profile_combo.addItem("Default")
    
    def on_profile_changed(self, profile_name):
        """Handle profile selection change."""
        if profile_name and profile_name != "Default":
            profile = self.profile_manager.get_profile(profile_name)
            if profile:
                self.apply_profile_to_settings(profile)
                self.log_message(f"Switched to profile: {profile_name}")
    
    def on_preset_changed(self, preset_name):
        """Handle gaming mode preset change."""
        if preset_name and preset_name != "Custom":
            # Create profile from preset
            preset_profile = None
            if preset_name == "FPS":
                preset_profile = GamingModePresets.create_fps_profile()
            elif preset_name == "MOBA":
                preset_profile = GamingModePresets.create_moba_profile()
            elif preset_name == "RTS":
                preset_profile = GamingModePresets.create_rts_profile()
            elif preset_name == "MMO":
                preset_profile = GamingModePresets.create_mmo_profile()
            elif preset_name == "Productivity":
                preset_profile = GamingModePresets.create_productivity_profile()
            
            if preset_profile:
                self.apply_profile_to_settings(preset_profile)
                self.log_message(f"Applied {preset_name} preset")
    
    def import_profile(self):
        """Import a profile from file."""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            profile = self.profile_exporter.import_profile(file_path)
            if profile:
                self.profile_manager.save_profile(profile)
                self.refresh_profile_list()
                self.log_message(f"Profile imported: {profile.metadata.name}")
            else:
                QMessageBox.warning(self, "Import Failed", "Failed to import profile")
    
    def export_profile(self):
        """Export current profile to file."""
        from PyQt5.QtWidgets import QFileDialog
        profile_name = self.profile_combo.currentText()
        if profile_name == "Default":
            QMessageBox.warning(self, "Export Failed", "Cannot export default profile")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile", f"{profile_name}.json", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            profile = self.profile_manager.get_profile(profile_name)
            if profile:
                success = self.profile_exporter.export_profile(profile, file_path)
                if success:
                    self.log_message(f"Profile exported: {profile_name}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export profile")
            else:
                QMessageBox.warning(self, "Export Failed", "Profile not found")
            
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click to show/hide window
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click to show context menu (this is handled automatically)
            pass
        elif reason == QSystemTrayIcon.MiddleClick:
            # Middle click to toggle optimization
            self.toggle_optimization_from_tray()
            
    def closeEvent(self, event):
        """Handle application close event."""
        if self.minimize_tray_checkbox.isChecked() and hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            self.hide()
            if self.notifications_checkbox.isChecked():
                self.tray_icon.showMessage(
                    "ZeroLag",
                    "Application minimized to system tray",
                    QSystemTrayIcon.Information,
                    2000
                )
            event.ignore()
        else:
            # Actually close the application
            self.stop_optimization()
            if hasattr(self, 'hotkey_manager'):
                self.stop_hotkeys()
            self.save_settings()
            event.accept()
            
    def changeEvent(self, event):
        """Handle window state change events."""
        if event.type() == event.WindowStateChange:
            if self.isMinimized() and self.minimize_tray_checkbox.isChecked():
                self.hide()
                if (hasattr(self, 'tray_icon') and self.tray_icon.isVisible() and 
                    hasattr(self, 'notifications_checkbox') and self.notifications_checkbox.isChecked()):
                    self.tray_icon.showMessage(
                        "ZeroLag",
                        "Application minimized to system tray",
                        QSystemTrayIcon.Information,
                        2000
                    )
    
    # Hotkey Management Methods
    def start_hotkeys(self):
        """Start hotkey detection."""
        try:
            if self.hotkey_manager and not self.hotkey_manager.is_running:
                self.hotkey_manager.start()
                self.emergency_hotkey_manager.start()
                
                self.start_hotkeys_btn.setEnabled(False)
                self.stop_hotkeys_btn.setEnabled(True)
                self.emergency_status_label.setText("Status: Active")
                self.emergency_status_label.setStyleSheet("color: #00d4ff; font-weight: 700; font-size: 14px;")
                self.update_tray_hotkey_status()
                
                self.log_message("Hotkey detection started")
                
        except Exception as e:
            self.log_message(f"Error starting hotkeys: {e}", "ERROR")
    
    def stop_hotkeys(self):
        """Stop hotkey detection."""
        try:
            if self.hotkey_manager and self.hotkey_manager.is_running:
                self.hotkey_manager.stop()
                self.emergency_hotkey_manager.stop()
                
                self.start_hotkeys_btn.setEnabled(True)
                self.stop_hotkeys_btn.setEnabled(False)
                self.emergency_status_label.setText("Status: Stopped")
                self.emergency_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                self.update_tray_hotkey_status()
                
                self.log_message("Hotkey detection stopped")
                
        except Exception as e:
            self.log_message(f"Error stopping hotkeys: {e}", "ERROR")
    
    def on_hotkey_profile_changed(self, profile_name):
        """Handle hotkey profile selection change."""
        if profile_name and profile_name != "Default":
            # Set active profile
            success = self.hotkey_config_manager.set_active_profile(profile_name)
            if success:
                self.refresh_hotkey_list()
                self.log_message(f"Switched to hotkey profile: {profile_name}")
            else:
                self.log_message(f"Failed to switch to hotkey profile: {profile_name}", "ERROR")
    
    def on_hotkey_preset_changed(self, preset_name):
        """Handle hotkey preset selection change."""
        if preset_name and preset_name != "Custom":
            # Apply preset
            preset = self.hotkey_preset_manager.get_preset(preset_name)
            if preset:
                # Create new profile from preset
                profile_name = f"{preset_name}_Preset"
                profile = self.hotkey_config_manager.create_profile(profile_name)
                
                # Apply preset bindings
                for binding in preset.bindings:
                    self.hotkey_config_manager.add_binding(profile_name, binding)
                
                self.refresh_hotkey_list()
                self.log_message(f"Applied {preset_name} hotkey preset")
    
    def create_hotkey_profile(self):
        """Create a new hotkey profile."""
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Hotkey Profile", "Profile name:")
        if ok and name:
            success = self.hotkey_config_manager.create_profile(name)
            if success:
                self.hotkey_profile_combo.addItem(name)
                self.hotkey_profile_combo.setCurrentText(name)
                self.log_message(f"Created hotkey profile: {name}")
            else:
                QMessageBox.warning(self, "Create Failed", f"Failed to create profile '{name}'")
    
    def delete_hotkey_profile(self):
        """Delete the current hotkey profile."""
        profile_name = self.hotkey_profile_combo.currentText()
        if profile_name != "Default":
            reply = QMessageBox.question(
                self, "Delete Profile",
                f"Are you sure you want to delete hotkey profile '{profile_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.hotkey_config_manager.delete_profile(profile_name)
                if success:
                    self.hotkey_profile_combo.removeItem(self.hotkey_profile_combo.currentIndex())
                    self.refresh_hotkey_list()
                    self.log_message(f"Deleted hotkey profile: {profile_name}")
                else:
                    QMessageBox.warning(self, "Delete Failed", f"Failed to delete profile '{profile_name}'")
        else:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the default profile.")
    
    def add_hotkey(self):
        """Add a new hotkey binding."""
        try:
            # Get current profile
            profile_name = self.hotkey_profile_combo.currentText()
            
            # Parse modifier and key
            modifier_text = self.modifier_combo.currentText()
            key_text = self.key_combo.currentText()
            action_text = self.action_combo.currentText()
            
            # Convert to hotkey format
            hotkey_string = f"{modifier_text}+{key_text}" if modifier_text != "None" else key_text
            
            # Convert action text to HotkeyActionType
            from src.core.hotkeys.hotkey_actions import HotkeyActionType
            action_type = HotkeyActionType.TOGGLE_ZEROLAG  # Default action
            
            # Convert modifier text to HotkeyModifier
            from src.core.hotkeys.hotkey_detector import HotkeyModifier
            modifiers = HotkeyModifier.NONE
            if "Ctrl" in modifier_text:
                modifiers |= HotkeyModifier.CTRL
            if "Alt" in modifier_text:
                modifiers |= HotkeyModifier.ALT
            if "Shift" in modifier_text:
                modifiers |= HotkeyModifier.SHIFT
            
            # Simple key mapping (this should be more comprehensive)
            key_map = {
                "F1": 112, "F2": 113, "F3": 114, "F4": 115, "F5": 116, "F6": 117,
                "F7": 118, "F8": 119, "F9": 120, "F10": 121, "F11": 122, "F12": 123,
                "Space": 32, "Enter": 13, "Tab": 9, "Esc": 27, "Delete": 46, "Backspace": 8
            }
            virtual_key = key_map.get(key_text, ord(key_text.upper()) if len(key_text) == 1 else 0)
            
            # Add to profile using the correct method signature
            binding = self.hotkey_config_manager.add_binding(
                profile_name, action_type, modifiers, virtual_key, key_text, f"{action_text} hotkey"
            )
            
            if binding:
                self.refresh_hotkey_list()
                self.log_message(f"Added hotkey: {hotkey_string} -> {action_text}")
            else:
                QMessageBox.warning(self, "Add Failed", f"Failed to add hotkey: {hotkey_string}")
                
        except Exception as e:
            self.log_message(f"Error adding hotkey: {e}", "ERROR")
    
    def remove_hotkey(self):
        """Remove selected hotkey."""
        # For now, just clear all hotkeys
        profile_name = self.hotkey_profile_combo.currentText()
        bindings = self.hotkey_config_manager.get_bindings(profile_name)
        success = True
        for hotkey_id in list(bindings.keys()):
            if not self.hotkey_config_manager.remove_binding(profile_name, hotkey_id):
                success = False
        
        if success:
            self.refresh_hotkey_list()
            self.log_message(f"Cleared hotkeys for profile: {profile_name}")
    
    def clear_hotkeys(self):
        """Clear all hotkeys in current profile."""
        profile_name = self.hotkey_profile_combo.currentText()
        bindings = self.hotkey_config_manager.get_bindings(profile_name)
        success = True
        for hotkey_id in list(bindings.keys()):
            if not self.hotkey_config_manager.remove_binding(profile_name, hotkey_id):
                success = False
        
        if success:
            self.refresh_hotkey_list()
            self.log_message(f"Cleared all hotkeys for profile: {profile_name}")
    
    def test_hotkey(self):
        """Test the currently selected hotkey."""
        # For now, just show a message
        QMessageBox.information(self, "Test Hotkey", "Hotkey test functionality will be implemented in the next version.")
    
    def refresh_hotkey_list(self):
        """Refresh the hotkey list display."""
        try:
            from src.core.hotkeys.hotkey_detector import HotkeyModifier
            
            profile_name = self.hotkey_profile_combo.currentText()
            bindings = self.hotkey_config_manager.get_bindings(profile_name)
            
            if bindings:
                hotkey_text = []
                for binding in bindings.values():
                    # Create hotkey string from modifiers and key
                    modifier_str = ""
                    if binding.modifiers & HotkeyModifier.CTRL:
                        modifier_str += "Ctrl+"
                    if binding.modifiers & HotkeyModifier.ALT:
                        modifier_str += "Alt+"
                    if binding.modifiers & HotkeyModifier.SHIFT:
                        modifier_str += "Shift+"
                    
                    hotkey_string = f"{modifier_str}{binding.key_name}"
                    hotkey_text.append(f"{hotkey_string} -> {binding.action_type.value}")
                self.hotkey_list.setText("\n".join(hotkey_text))
            else:
                self.hotkey_list.setText("No hotkeys configured")
                
        except Exception as e:
            self.log_message(f"Error refreshing hotkey list: {e}", "ERROR")
    
    # Community Profile Sharing Methods
    
    def init_community_sharing(self):
        """Initialize community profile sharing components."""
        try:
            # Initialize profile library manager
            library_path = Path("profiles/community")
            self.profile_library_manager = ProfileLibraryManager(library_path)
            
            # Initialize GitHub repository (if configured)
            # Note: In a real implementation, this would load from config
            github_config = ProfileRepositoryConfig(
                owner="zerolag-community",
                repo="profiles",
                token="",  # Would be loaded from secure config
                branch="main"
            )
            
            if github_config.token:
                repository = GitHubProfileRepository(github_config)
                self.profile_sharing_manager = ProfileSharingManager(repository)
                self.profile_library_manager.repository_client = repository
            
            # Refresh upload profile list
            self.refresh_upload_profile_list()
            
            self.log_message("Community profile sharing initialized")
            
        except Exception as e:
            self.log_message(f"Error initializing community sharing: {e}", "ERROR")
    
    def search_community_profiles(self):
        """Search for community profiles."""
        try:
            if not self.profile_library_manager:
                QMessageBox.warning(self, "Error", "Community sharing not initialized")
                return
            
            # Get search filters
            search_text = self.community_search_edit.toPlainText().strip()
            category = self.category_filter_combo.currentText()
            difficulty = self.difficulty_filter_combo.currentText()
            sort_by = self.sort_filter_combo.currentText()
            
            # Create search filter
            filters = ProfileSearchFilter()
            
            if search_text:
                filters.search_text = search_text
            
            if category != "All":
                filters.categories.add(ProfileCategory(category.lower()))
            
            if difficulty != "All":
                filters.difficulties.add(ProfileDifficulty(difficulty.lower()))
            
            # Set sort order
            sort_mapping = {
                "Newest": SortOrder.NEWEST,
                "Most Downloaded": SortOrder.MOST_DOWNLOADED,
                "Highest Rated": SortOrder.HIGHEST_RATED,
                "Alphabetical": SortOrder.ALPHABETICAL
            }
            filters.sort_order = sort_mapping.get(sort_by, SortOrder.NEWEST)
            
            # Search profiles
            profiles = self.profile_library_manager.search_profiles(filters)
            
            # Display results
            self.display_community_profiles(profiles)
            
            self.community_status_label.setText(f"Found {len(profiles)} profiles")
            
        except Exception as e:
            self.log_message(f"Error searching community profiles: {e}", "ERROR")
            QMessageBox.critical(self, "Search Error", f"Error searching profiles: {e}")
    
    def display_community_profiles(self, profiles):
        """Display community profiles in the list."""
        try:
            if not profiles:
                self.community_profile_list.setText("No profiles found matching your criteria.")
                self.download_profile_btn.setEnabled(False)
                return
            
            # Format profiles for display
            profile_text = ""
            for i, profile in enumerate(profiles):
                profile_text += f"{i+1}. {profile.name} by {profile.author}\n"
                profile_text += f"   Category: {profile.category.value.title()} | "
                profile_text += f"Difficulty: {profile.difficulty.value.title()} | "
                profile_text += f"Rating: {profile.rating:.1f}/5.0 ({profile.rating_count} votes)\n"
                profile_text += f"   Downloads: {profile.downloads} | "
                profile_text += f"Tags: {', '.join(profile.tags[:3])}\n"
                profile_text += f"   Description: {profile.description[:100]}...\n\n"
            
            self.community_profile_list.setText(profile_text)
            self.download_profile_btn.setEnabled(True)
            
        except Exception as e:
            self.log_message(f"Error displaying community profiles: {e}", "ERROR")
    
    def download_community_profile(self):
        """Download the selected community profile."""
        try:
            if not self.profile_library_manager:
                QMessageBox.warning(self, "Error", "Community sharing not initialized")
                return
            
            # Get selected profile (simplified - in real implementation would track selection)
            selected_text = self.community_profile_list.toPlainText()
            if not selected_text or "No profiles found" in selected_text:
                QMessageBox.warning(self, "No Selection", "Please search for profiles first")
                return
            
            # For now, download the first profile (in real implementation, track selection)
            profiles = self.profile_library_manager.search_profiles(ProfileSearchFilter())
            if not profiles:
                QMessageBox.warning(self, "No Profiles", "No profiles available to download")
                return
            
            profile = profiles[0]  # Simplified selection
            
            # Download profile
            downloaded_profile = self.profile_library_manager.download_profile(profile.profile_id)
            if downloaded_profile:
                # Convert to regular profile and load
                regular_profile = Profile.from_dict(downloaded_profile.profile_data)
                self.profile_manager.save_profile(regular_profile)
                self.refresh_profile_list()
                
                QMessageBox.information(self, "Success", f"Downloaded profile: {downloaded_profile.name}")
                self.log_message(f"Downloaded community profile: {downloaded_profile.name}")
            else:
                QMessageBox.warning(self, "Download Failed", "Failed to download profile")
                
        except Exception as e:
            self.log_message(f"Error downloading community profile: {e}", "ERROR")
            QMessageBox.critical(self, "Download Error", f"Error downloading profile: {e}")
    
    def refresh_community_library(self):
        """Refresh the local community library."""
        try:
            if not self.profile_library_manager:
                QMessageBox.warning(self, "Error", "Community sharing not initialized")
                return
            
            # Get library stats
            stats = self.profile_library_manager.get_library_stats()
            
            # Display featured profiles
            featured_profiles = self.profile_library_manager.get_featured_profiles()
            self.display_community_profiles(featured_profiles)
            
            self.community_status_label.setText(f"Library: {stats['total_profiles']} profiles")
            
        except Exception as e:
            self.log_message(f"Error refreshing community library: {e}", "ERROR")
    
    def sync_community_library(self):
        """Sync the local library with the remote repository."""
        try:
            if not self.profile_library_manager:
                QMessageBox.warning(self, "Error", "Community sharing not initialized")
                return
            
            self.community_status_label.setText("Syncing with repository...")
            
            # Sync with repository
            success = self.profile_library_manager.sync_with_repository()
            
            if success:
                self.community_status_label.setText("Sync completed")
                self.refresh_community_library()
                QMessageBox.information(self, "Sync Complete", "Library synchronized with repository")
            else:
                self.community_status_label.setText("Sync failed")
                QMessageBox.warning(self, "Sync Failed", "Failed to sync with repository")
                
        except Exception as e:
            self.log_message(f"Error syncing community library: {e}", "ERROR")
            QMessageBox.critical(self, "Sync Error", f"Error syncing library: {e}")
    
    def refresh_upload_profile_list(self):
        """Refresh the list of profiles available for upload."""
        try:
            # Get all local profiles
            profiles = self.profile_manager.get_all_profiles()
            
            # Update combo box
            self.upload_profile_combo.clear()
            self.upload_profile_combo.addItems([profile.name for profile in profiles])
            
        except Exception as e:
            self.log_message(f"Error refreshing upload profile list: {e}", "ERROR")
    
    def on_upload_profile_changed(self, profile_name):
        """Handle upload profile selection change."""
        try:
            if profile_name:
                # Load profile and populate metadata
                profile = self.profile_manager.get_profile(profile_name)
                if profile:
                    self.upload_name_edit.setText(profile.name)
                    self.upload_description_edit.setText(f"Profile optimized for {profile.settings.gaming_mode.value} gaming")
                    self.upload_profile_btn.setEnabled(True)
                else:
                    self.upload_profile_btn.setEnabled(False)
            else:
                self.upload_profile_btn.setEnabled(False)
                
        except Exception as e:
            self.log_message(f"Error handling upload profile change: {e}", "ERROR")
    
    def validate_upload_profile(self):
        """Validate the profile before upload."""
        try:
            profile_name = self.upload_profile_combo.currentText()
            if not profile_name:
                QMessageBox.warning(self, "No Profile", "Please select a profile to validate")
                return
            
            profile = self.profile_manager.get_profile(profile_name)
            if not profile:
                QMessageBox.warning(self, "Profile Not Found", "Selected profile not found")
                return
            
            # Validate profile
            validation_result = self.profile_validator.validate_profile(profile.to_dict())
            
            # Display validation results
            if validation_result.is_valid:
                QMessageBox.information(self, "Validation Passed", 
                    f"Profile validation passed!\nCompatibility Score: {validation_result.compatibility_score:.2f}")
            else:
                issues_text = "\n".join([f"- {issue.message}" for issue in validation_result.issues])
                QMessageBox.warning(self, "Validation Issues", 
                    f"Profile validation found issues:\n\n{issues_text}")
            
        except Exception as e:
            self.log_message(f"Error validating upload profile: {e}", "ERROR")
            QMessageBox.critical(self, "Validation Error", f"Error validating profile: {e}")
    
    def upload_community_profile(self):
        """Upload a profile to the community library."""
        try:
            if not self.profile_sharing_manager:
                QMessageBox.warning(self, "Error", "Community sharing not initialized")
                return
            
            profile_name = self.upload_profile_combo.currentText()
            if not profile_name:
                QMessageBox.warning(self, "No Profile", "Please select a profile to upload")
                return
            
            profile = self.profile_manager.get_profile(profile_name)
            if not profile:
                QMessageBox.warning(self, "Profile Not Found", "Selected profile not found")
                return
            
            # Get upload metadata
            metadata = {
                "name": self.upload_name_edit.toPlainText().strip() or profile.name,
                "description": self.upload_description_edit.toPlainText().strip(),
                "category": self.upload_category_combo.currentText().lower(),
                "difficulty": self.upload_difficulty_combo.currentText().lower(),
                "tags": [tag.strip() for tag in self.upload_tags_edit.toPlainText().split(",") if tag.strip()],
                "author": "ZeroLag User",  # Would be loaded from user config
                "author_id": "user_001",  # Would be loaded from user config
                "compatibility": ["windows", "linux", "darwin"],
                "requirements": {}
            }
            
            # Validate required fields
            if not metadata["name"]:
                QMessageBox.warning(self, "Invalid Data", "Profile name is required")
                return
            
            if not metadata["description"]:
                QMessageBox.warning(self, "Invalid Data", "Profile description is required")
                return
            
            # Upload profile
            self.community_status_label.setText("Uploading profile...")
            
            profile_id = self.profile_sharing_manager.upload_profile(profile, metadata)
            
            if profile_id:
                self.community_status_label.setText("Upload completed")
                QMessageBox.information(self, "Upload Success", 
                    f"Profile uploaded successfully!\nProfile ID: {profile_id}")
                self.log_message(f"Uploaded community profile: {metadata['name']}")
            else:
                self.community_status_label.setText("Upload failed")
                QMessageBox.warning(self, "Upload Failed", "Failed to upload profile")
                
        except Exception as e:
            self.log_message(f"Error uploading community profile: {e}", "ERROR")
            QMessageBox.critical(self, "Upload Error", f"Error uploading profile: {e}")
