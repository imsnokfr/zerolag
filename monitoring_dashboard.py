#!/usr/bin/env python3
"""
ZeroLag Comprehensive Monitoring Dashboard

This dashboard provides real-time monitoring of:
- Application performance
- User feedback
- System health
- Error tracking
- Release metrics
"""

import sys
import os
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QPushButton, QTextEdit, QTabWidget, QTableWidget, 
    QTableWidgetItem, QProgressBar, QGroupBox, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QSystemTrayIcon,
    QMenu, QAction, QMessageBox, QStatusBar
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

from src.core.monitoring.performance_monitor import PerformanceMonitor
from src.core.monitoring.crash_reporter import CrashReporter
from src.core.feedback.feedback_manager import FeedbackManager
from src.core.analysis.performance_analyzer import PerformanceAnalyzer


class MonitoringData:
    """Container for monitoring data."""
    
    def __init__(self):
        self.performance_metrics = {}
        self.feedback_stats = {}
        self.error_logs = []
        self.system_health = {}
        self.release_metrics = {}
        self.last_update = datetime.now()


class PerformanceWidget(QWidget):
    """Widget for displaying performance metrics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.monitor = PerformanceMonitor()
    
    def setup_ui(self):
        """Setup the performance widget UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Performance Metrics")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Metrics grid
        metrics_group = QGroupBox("Real-time Metrics")
        metrics_layout = QGridLayout()
        
        # CPU Usage
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        metrics_layout.addWidget(self.cpu_label, 0, 0)
        metrics_layout.addWidget(self.cpu_progress, 0, 1)
        
        # Memory Usage
        self.memory_label = QLabel("Memory Usage:")
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        metrics_layout.addWidget(self.memory_label, 1, 0)
        metrics_layout.addWidget(self.memory_progress, 1, 1)
        
        # Input Lag
        self.lag_label = QLabel("Input Lag:")
        self.lag_value = QLabel("0.0 ms")
        metrics_layout.addWidget(self.lag_label, 2, 0)
        metrics_layout.addWidget(self.lag_value, 2, 1)
        
        # Frame Rate
        self.fps_label = QLabel("Frame Rate:")
        self.fps_value = QLabel("0.0 FPS")
        metrics_layout.addWidget(self.fps_label, 3, 0)
        metrics_layout.addWidget(self.fps_value, 3, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Performance history
        history_group = QGroupBox("Performance History")
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(200)
        history_layout.addWidget(self.history_text)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        self.setLayout(layout)
        
        # Start monitoring
        self.monitor.start_monitoring()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Update every second
    
    def update_metrics(self):
        """Update performance metrics display."""
        try:
            metrics = self.monitor.get_current_metrics()
            if metrics:
                # Update progress bars
                self.cpu_progress.setValue(int(metrics.cpu_percent))
                self.memory_progress.setValue(int(metrics.memory_percent))
                
                # Update values
                self.lag_value.setText(f"{metrics.input_lag_ms:.1f} ms")
                self.fps_value.setText(f"{metrics.frame_rate_fps:.1f} FPS")
                
                # Update history
                timestamp = datetime.now().strftime("%H:%M:%S")
                history_entry = f"[{timestamp}] CPU: {metrics.cpu_percent:.1f}% | Memory: {metrics.memory_percent:.1f}% | Lag: {metrics.input_lag_ms:.1f}ms | FPS: {metrics.frame_rate_fps:.1f}"
                
                self.history_text.append(history_entry)
                
                # Keep only last 50 entries
                lines = self.history_text.toPlainText().split('\n')
                if len(lines) > 50:
                    self.history_text.setPlainText('\n'.join(lines[-50:]))
                
        except Exception as e:
            print(f"Error updating performance metrics: {e}")


class FeedbackWidget(QWidget):
    """Widget for displaying feedback and user data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.feedback_manager = FeedbackManager()
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_feedback)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup the feedback widget UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Feedback & User Data")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Statistics
        stats_group = QGroupBox("Feedback Statistics")
        stats_layout = QGridLayout()
        
        self.total_feedback_label = QLabel("Total Feedback:")
        self.total_feedback_value = QLabel("0")
        stats_layout.addWidget(self.total_feedback_label, 0, 0)
        stats_layout.addWidget(self.total_feedback_value, 0, 1)
        
        self.resolution_rate_label = QLabel("Resolution Rate:")
        self.resolution_rate_value = QLabel("0%")
        stats_layout.addWidget(self.resolution_rate_label, 1, 0)
        stats_layout.addWidget(self.resolution_rate_value, 1, 1)
        
        self.average_rating_label = QLabel("Average Rating:")
        self.average_rating_value = QLabel("0.0/5.0")
        stats_layout.addWidget(self.average_rating_label, 2, 0)
        stats_layout.addWidget(self.average_rating_value, 2, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Recent feedback table
        feedback_group = QGroupBox("Recent Feedback")
        feedback_layout = QVBoxLayout()
        
        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(4)
        self.feedback_table.setHorizontalHeaderLabels(["Time", "Type", "Rating", "Summary"])
        self.feedback_table.horizontalHeader().setStretchLastSection(True)
        feedback_layout.addWidget(self.feedback_table)
        
        feedback_group.setLayout(feedback_layout)
        layout.addWidget(feedback_group)
        
        self.setLayout(layout)
    
    def update_feedback(self):
        """Update feedback display."""
        try:
            stats = self.feedback_manager.get_feedback_stats()
            
            # Update statistics
            self.total_feedback_value.setText(str(stats.total_feedback))
            self.resolution_rate_value.setText(f"{stats.resolution_rate:.1f}%")
            self.average_rating_value.setText(f"{stats.average_rating:.1f}/5.0")
            
            # Update feedback table
            recent_feedback = self.feedback_manager.get_recent_feedback(limit=20)
            self.feedback_table.setRowCount(len(recent_feedback))
            
            for row, feedback in enumerate(recent_feedback):
                timestamp = feedback.timestamp.strftime("%H:%M:%S")
                self.feedback_table.setItem(row, 0, QTableWidgetItem(timestamp))
                self.feedback_table.setItem(row, 1, QTableWidgetItem(feedback.feedback_type))
                self.feedback_table.setItem(row, 2, QTableWidgetItem(str(feedback.rating)))
                self.feedback_table.setItem(row, 3, QTableWidgetItem(feedback.summary[:50] + "..."))
            
        except Exception as e:
            print(f"Error updating feedback: {e}")


class ErrorWidget(QWidget):
    """Widget for displaying errors and system health."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.crash_reporter = CrashReporter()
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_errors)
        self.update_timer.start(10000)  # Update every 10 seconds
    
    def setup_ui(self):
        """Setup the error widget UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("System Health & Errors")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # System health
        health_group = QGroupBox("System Health")
        health_layout = QGridLayout()
        
        self.system_status_label = QLabel("System Status:")
        self.system_status_value = QLabel("Healthy")
        self.system_status_value.setStyleSheet("color: green; font-weight: bold;")
        health_layout.addWidget(self.system_status_label, 0, 0)
        health_layout.addWidget(self.system_status_value, 0, 1)
        
        self.error_count_label = QLabel("Error Count:")
        self.error_count_value = QLabel("0")
        health_layout.addWidget(self.error_count_label, 1, 0)
        health_layout.addWidget(self.error_count_value, 1, 1)
        
        self.last_error_label = QLabel("Last Error:")
        self.last_error_value = QLabel("None")
        health_layout.addWidget(self.last_error_label, 2, 0)
        health_layout.addWidget(self.last_error_value, 2, 1)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # Error log
        error_group = QGroupBox("Error Log")
        error_layout = QVBoxLayout()
        
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setMaximumHeight(300)
        error_layout.addWidget(self.error_text)
        
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)
        
        self.setLayout(layout)
    
    def update_errors(self):
        """Update error display."""
        try:
            # Get error statistics
            error_stats = self.crash_reporter.get_error_stats()
            
            # Update system health
            if error_stats.total_errors == 0:
                self.system_status_value.setText("Healthy")
                self.system_status_value.setStyleSheet("color: green; font-weight: bold;")
            elif error_stats.total_errors < 5:
                self.system_status_value.setText("Warning")
                self.system_status_value.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.system_status_value.setText("Critical")
                self.system_status_value.setStyleSheet("color: red; font-weight: bold;")
            
            self.error_count_value.setText(str(error_stats.total_errors))
            
            if error_stats.last_error:
                self.last_error_value.setText(error_stats.last_error.error_type)
            else:
                self.last_error_value.setText("None")
            
            # Update error log
            recent_errors = self.crash_reporter.get_recent_errors(limit=20)
            error_log = ""
            for error in recent_errors:
                timestamp = error.timestamp.strftime("%H:%M:%S")
                error_log += f"[{timestamp}] {error.error_type}: {error.message}\n"
            
            self.error_text.setPlainText(error_log)
            
        except Exception as e:
            print(f"Error updating error display: {e}")


class MonitoringDashboard(QMainWindow):
    """Main monitoring dashboard window."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_system_tray()
        self.setup_status_bar()
    
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("ZeroLag Monitoring Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("ZeroLag Monitoring Dashboard")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Performance tab
        self.performance_widget = PerformanceWidget()
        self.tab_widget.addTab(self.performance_widget, "Performance")
        
        # Feedback tab
        self.feedback_widget = FeedbackWidget()
        self.tab_widget.addTab(self.feedback_widget, "Feedback")
        
        # Errors tab
        self.error_widget = ErrorWidget()
        self.tab_widget.addTab(self.error_widget, "System Health")
        
        layout.addWidget(self.tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh All")
        self.refresh_btn.clicked.connect(self.refresh_all)
        button_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_btn)
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
    
    def setup_system_tray(self):
        """Setup system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show Dashboard", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide Dashboard", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip("ZeroLag Monitoring Dashboard")
            self.tray_icon.show()
    
    def setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Update status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def refresh_all(self):
        """Refresh all monitoring data."""
        self.status_label.setText("Refreshing...")
        
        # Refresh each widget
        self.performance_widget.update_metrics()
        self.feedback_widget.update_feedback()
        self.error_widget.update_errors()
        
        self.status_label.setText("Refreshed")
    
    def export_data(self):
        """Export monitoring data."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_data_{timestamp}.json"
            
            # Collect data from all widgets
            data = {
                "timestamp": timestamp,
                "performance": self.performance_widget.monitor.get_current_metrics().__dict__ if self.performance_widget.monitor else {},
                "feedback": self.feedback_widget.feedback_manager.get_feedback_stats().__dict__,
                "errors": [error.__dict__ for error in self.error_widget.crash_reporter.get_recent_errors(limit=100)]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.status_label.setText(f"Data exported to {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(self, "Settings", "Settings dialog not implemented yet.")
    
    def update_status(self):
        """Update status bar."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"Last updated: {current_time}")
    
    def quit_application(self):
        """Quit the application."""
        self.close()
    
    def closeEvent(self, event):
        """Handle close event."""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.hide()
            event.ignore()
        else:
            event.accept()


def main():
    """Main function."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ZeroLag Monitoring Dashboard")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ZeroLag")
    
    # Create and show dashboard
    dashboard = MonitoringDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
