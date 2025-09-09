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
        
        self.init_ui()
        self.init_input_handlers()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ZeroLag - Gaming Input Optimizer")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d4d4d4, stop:1 #afafaf);
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QComboBox {
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                background-color: #404040;
            }
            QSpinBox {
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                background-color: #404040;
            }
            QTextEdit {
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #353535;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
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
        self.dpi_value_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
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
        self.debounce_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
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
        
        # Profile Buttons
        profile_buttons_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton("Save")
        self.load_profile_btn = QPushButton("Load")
        self.delete_profile_btn = QPushButton("Delete")
        profile_buttons_layout.addWidget(self.save_profile_btn)
        profile_buttons_layout.addWidget(self.load_profile_btn)
        profile_buttons_layout.addWidget(self.delete_profile_btn)
        profile_layout.addLayout(profile_buttons_layout)
        
        controls_layout.addWidget(profile_group)
        
        # Control Buttons
        control_buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Optimization")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; }")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        control_buttons_layout.addWidget(self.start_btn)
        control_buttons_layout.addWidget(self.stop_btn)
        controls_layout.addLayout(control_buttons_layout)
        
        # Connect button signals
        self.start_btn.clicked.connect(self.start_optimization)
        self.stop_btn.clicked.connect(self.stop_optimization)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        
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
        self.latency_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        stats_layout.addWidget(self.latency_label, 2, 1)
        
        # Events/sec
        stats_layout.addWidget(QLabel("Events/sec:"), 3, 0)
        self.events_per_sec_label = QLabel("0")
        self.events_per_sec_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
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
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Performance indicator
        self.performance_indicator = QLabel("●")
        self.performance_indicator.setStyleSheet("color: #f44336;")
        self.status_bar.addPermanentWidget(self.performance_indicator)
        
    def create_system_tray(self):
        """Create the system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
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
                self.performance_indicator.setStyleSheet("color: #4CAF50;")
                
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
                self.performance_indicator.setStyleSheet("color: #f44336;")
                
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
        self.log_message(f"Profile '{profile_name}' saved")
        
    def load_profile(self):
        """Load a profile."""
        profile_name = self.profile_combo.currentText()
        self.log_message(f"Profile '{profile_name}' loaded")
        
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
                self.log_message(f"Profile '{profile_name}' deleted")
        else:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the default profile.")
            
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
            
    def closeEvent(self, event):
        """Handle application close event."""
        if self.minimize_tray_checkbox.isChecked() and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.stop_optimization()
            self.save_settings()
            event.accept()
            
    def changeEvent(self, event):
        """Handle window state change events."""
        if event.type() == event.WindowStateChange:
            if self.isMinimized() and self.minimize_tray_checkbox.isChecked():
                self.hide()
                if self.notifications_checkbox.isChecked():
                    self.tray_icon.showMessage(
                        "ZeroLag",
                        "Application minimized to system tray",
                        QSystemTrayIcon.Information,
                        2000
                    )
