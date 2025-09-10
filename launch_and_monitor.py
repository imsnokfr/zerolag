#!/usr/bin/env python3
"""
ZeroLag Launch and Monitoring Script

This script launches ZeroLag and provides comprehensive monitoring
and feedback collection capabilities.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import threading
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit, QTabWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon

from src.gui.main_window import ZeroLagMainWindow
from src.core.feedback.feedback_manager import FeedbackManager
from src.core.monitoring.performance_monitor import PerformanceMonitor
from src.core.monitoring.crash_reporter import CrashReporter
from src.core.analysis.performance_analyzer import PerformanceAnalyzer


class MonitoringThread(QThread):
    """Thread for monitoring system performance and feedback."""
    
    performance_updated = pyqtSignal(dict)
    feedback_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.performance_monitor = None
        self.feedback_manager = None
        self.crash_reporter = None
    
    def run(self):
        """Run monitoring loop."""
        self.running = True
        
        try:
            # Initialize monitoring components
            self.performance_monitor = PerformanceMonitor(monitoring_interval=5.0)
            self.feedback_manager = FeedbackManager()
            self.crash_reporter = CrashReporter()
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            # Monitoring loop
            while self.running:
                try:
                    # Get performance metrics
                    current_metrics = self.performance_monitor.get_current_metrics()
                    if current_metrics:
                        self.performance_updated.emit({
                            'cpu_percent': current_metrics.cpu_percent,
                            'memory_percent': current_metrics.memory_percent,
                            'input_lag_ms': current_metrics.input_lag_ms,
                            'frame_rate_fps': current_metrics.frame_rate_fps
                        })
                    
                    # Get feedback statistics
                    feedback_stats = self.feedback_manager.get_feedback_stats()
                    self.feedback_updated.emit({
                        'total_feedback': feedback_stats.total_feedback,
                        'resolution_rate': feedback_stats.resolution_rate,
                        'average_rating': feedback_stats.average_rating
                    })
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    self.error_occurred.emit(f"Monitoring error: {str(e)}")
                    time.sleep(5)
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize monitoring: {str(e)}")
        finally:
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.wait()


class LaunchMonitorWindow(QMainWindow):
    """Main window for launch and monitoring."""
    
    def __init__(self):
        super().__init__()
        self.zerolag_window = None
        self.monitoring_thread = None
        self.feedback_manager = FeedbackManager()
        self.setup_ui()
        self.setup_monitoring()
        self.setup_system_tray()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("ZeroLag Launch Monitor")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("ZeroLag Launch Monitor")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.launch_btn = QPushButton("Launch ZeroLag")
        self.launch_btn.clicked.connect(self.launch_zerolag)
        self.launch_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        button_layout.addWidget(self.launch_btn)
        
        self.monitor_btn = QPushButton("Start Monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        button_layout.addWidget(self.monitor_btn)
        
        self.feedback_btn = QPushButton("Open Feedback Dashboard")
        self.feedback_btn.clicked.connect(self.open_feedback_dashboard)
        self.feedback_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        button_layout.addWidget(self.feedback_btn)
        
        layout.addLayout(button_layout)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(200)
        layout.addWidget(self.status_text)
        
        # Performance metrics
        metrics_label = QLabel("Performance Metrics:")
        metrics_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(metrics_label)
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(150)
        layout.addWidget(self.metrics_text)
        
        # Feedback statistics
        feedback_label = QLabel("Feedback Statistics:")
        feedback_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(feedback_label)
        
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setMaximumHeight(150)
        layout.addWidget(self.feedback_text)
        
        central_widget.setLayout(layout)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def setup_monitoring(self):
        """Setup monitoring thread."""
        self.monitoring_thread = MonitoringThread()
        self.monitoring_thread.performance_updated.connect(self.update_performance_metrics)
        self.monitoring_thread.feedback_updated.connect(self.update_feedback_stats)
        self.monitoring_thread.error_occurred.connect(self.handle_error)
    
    def setup_system_tray(self):
        """Setup system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create tray menu
            tray_menu = QMenu()
            
            launch_action = QAction("Launch ZeroLag", self)
            launch_action.triggered.connect(self.launch_zerolag)
            tray_menu.addAction(launch_action)
            
            monitor_action = QAction("Toggle Monitoring", self)
            monitor_action.triggered.connect(self.toggle_monitoring)
            tray_menu.addAction(monitor_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip("ZeroLag Launch Monitor")
            self.tray_icon.show()
    
    def launch_zerolag(self):
        """Launch ZeroLag application."""
        try:
            if self.zerolag_window is None or not self.zerolag_window.isVisible():
                self.zerolag_window = ZeroLagMainWindow()
                self.zerolag_window.show()
                self.log_status("ZeroLag launched successfully")
            else:
                self.zerolag_window.raise_()
                self.zerolag_window.activateWindow()
                self.log_status("ZeroLag window brought to front")
        except Exception as e:
            self.log_status(f"Failed to launch ZeroLag: {str(e)}")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if self.monitoring_thread.isRunning():
            self.monitoring_thread.stop()
            self.monitor_btn.setText("Start Monitoring")
            self.log_status("Monitoring stopped")
        else:
            self.monitoring_thread.start()
            self.monitor_btn.setText("Stop Monitoring")
            self.log_status("Monitoring started")
    
    def open_feedback_dashboard(self):
        """Open feedback dashboard."""
        try:
            from src.gui.feedback_dashboard import FeedbackDashboard
            dashboard = FeedbackDashboard()
            dashboard.show()
            self.log_status("Feedback dashboard opened")
        except Exception as e:
            self.log_status(f"Failed to open feedback dashboard: {str(e)}")
    
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """Update performance metrics display."""
        metrics_text = f"""CPU Usage: {metrics.get('cpu_percent', 0):.1f}%
Memory Usage: {metrics.get('memory_percent', 0):.1f}%
Input Lag: {metrics.get('input_lag_ms', 0):.1f}ms
Frame Rate: {metrics.get('frame_rate_fps', 0):.1f} FPS"""
        
        self.metrics_text.setPlainText(metrics_text)
    
    def update_feedback_stats(self, stats: Dict[str, Any]):
        """Update feedback statistics display."""
        feedback_text = f"""Total Feedback: {stats.get('total_feedback', 0)}
Resolution Rate: {stats.get('resolution_rate', 0):.1f}%
Average Rating: {stats.get('average_rating', 0):.1f}/5.0"""
        
        self.feedback_text.setPlainText(feedback_text)
    
    def handle_error(self, error_message: str):
        """Handle monitoring errors."""
        self.log_status(f"Error: {error_message}")
    
    def log_status(self, message: str):
        """Log status message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Keep only last 50 lines
        lines = self.status_text.toPlainText().split('\n')
        if len(lines) > 50:
            self.status_text.setPlainText('\n'.join(lines[-50:]))
    
    def update_status(self):
        """Update status display."""
        # Check if ZeroLag is running
        if self.zerolag_window and self.zerolag_window.isVisible():
            self.launch_btn.setText("ZeroLag Running")
            self.launch_btn.setEnabled(False)
        else:
            self.launch_btn.setText("Launch ZeroLag")
            self.launch_btn.setEnabled(True)
        
        # Check monitoring status
        if self.monitoring_thread and self.monitoring_thread.isRunning():
            self.monitor_btn.setText("Stop Monitoring")
        else:
            self.monitor_btn.setText("Start Monitoring")
    
    def quit_application(self):
        """Quit the application."""
        if self.monitoring_thread and self.monitoring_thread.isRunning():
            self.monitoring_thread.stop()
        
        if self.zerolag_window:
            self.zerolag_window.close()
        
        self.close()
    
    def closeEvent(self, event):
        """Handle close event."""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.hide()
            event.ignore()
        else:
            self.quit_application()
            event.accept()


def main():
    """Main function."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ZeroLag Launch Monitor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ZeroLag")
    
    # Create and show main window
    window = LaunchMonitorWindow()
    window.show()
    
    # Start monitoring automatically
    window.toggle_monitoring()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
