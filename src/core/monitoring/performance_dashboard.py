"""
Real-Time Performance Dashboard for ZeroLag

This module provides a GUI dashboard for monitoring performance metrics
in real-time, displaying CPU usage, memory consumption, event processing
rates, and other key performance indicators.

Features:
- Real-time metric visualization
- Performance target tracking
- Alert notifications
- Historical trend display
- Export capabilities
- Customizable refresh rates
"""

import sys
import time
import threading
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QProgressBar,
                             QPushButton, QTextEdit, QGroupBox, QSpinBox,
                             QCheckBox, QFileDialog, QMessageBox, QTabWidget)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor

from .performance_monitor import PerformanceMonitor, PerformanceSnapshot, PerformanceAlert


class PerformanceDashboard(QMainWindow):
    """
    Real-time performance dashboard for monitoring ZeroLag metrics.
    
    Provides a comprehensive view of system performance including
    CPU usage, memory consumption, event processing rates, and alerts.
    """
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        """
        Initialize the performance dashboard.
        
        Args:
            performance_monitor: PerformanceMonitor instance to display data from
        """
        super().__init__()
        
        self.performance_monitor = performance_monitor
        self.update_timer = QTimer()
        self.alert_count = 0
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_styling()
        
        # Start update timer
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        # Add alert callback
        self.performance_monitor.add_alert_callback(self.on_alert)
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("ZeroLag Performance Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Overview tab
        overview_tab = self.create_overview_tab()
        tab_widget.addTab(overview_tab, "Overview")
        
        # Metrics tab
        metrics_tab = self.create_metrics_tab()
        tab_widget.addTab(metrics_tab, "Detailed Metrics")
        
        # Alerts tab
        alerts_tab = self.create_alerts_tab()
        tab_widget.addTab(alerts_tab, "Alerts")
        
        # Controls tab
        controls_tab = self.create_controls_tab()
        tab_widget.addTab(controls_tab, "Controls")
        
        # Status bar
        self.statusBar().showMessage("Performance monitoring active")
    
    def create_overview_tab(self) -> QWidget:
        """Create the overview tab with key metrics."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Performance Overview")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Key metrics grid
        metrics_group = QGroupBox("Key Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU Usage
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_value = QLabel("0.0%")
        metrics_layout.addWidget(self.cpu_label, 0, 0)
        metrics_layout.addWidget(self.cpu_progress, 0, 1)
        metrics_layout.addWidget(self.cpu_value, 0, 2)
        
        # Memory Usage
        self.memory_label = QLabel("Memory Usage:")
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.memory_value = QLabel("0.0 MB")
        metrics_layout.addWidget(self.memory_label, 1, 0)
        metrics_layout.addWidget(self.memory_progress, 1, 1)
        metrics_layout.addWidget(self.memory_value, 1, 2)
        
        # Events per Second
        self.events_label = QLabel("Events/sec:")
        self.events_progress = QProgressBar()
        self.events_progress.setMaximum(2000)
        self.events_value = QLabel("0")
        metrics_layout.addWidget(self.events_label, 2, 0)
        metrics_layout.addWidget(self.events_progress, 2, 1)
        metrics_layout.addWidget(self.events_value, 2, 2)
        
        # Queue Size
        self.queue_label = QLabel("Queue Size:")
        self.queue_progress = QProgressBar()
        self.queue_progress.setMaximum(1000)
        self.queue_value = QLabel("0")
        metrics_layout.addWidget(self.queue_label, 3, 0)
        metrics_layout.addWidget(self.queue_progress, 3, 1)
        metrics_layout.addWidget(self.queue_value, 3, 2)
        
        layout.addWidget(metrics_group)
        
        # Performance targets
        targets_group = QGroupBox("Performance Targets")
        targets_layout = QGridLayout(targets_group)
        
        self.targets_status = {}
        targets = [
            ("CPU < 1%", "cpu_target"),
            ("Memory < 50MB", "memory_target"),
            ("Events > 1000/sec", "events_target"),
            ("Drop Rate < 1%", "drop_target")
        ]
        
        for i, (label_text, key) in enumerate(targets):
            label = QLabel(label_text)
            status = QLabel("●")
            status.setStyleSheet("color: gray; font-size: 20px;")
            self.targets_status[key] = status
            targets_layout.addWidget(label, i, 0)
            targets_layout.addWidget(status, i, 1)
        
        layout.addWidget(targets_group)
        
        # Uptime
        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.uptime_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.uptime_label)
        
        layout.addStretch()
        return widget
    
    def create_metrics_tab(self) -> QWidget:
        """Create the detailed metrics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Detailed Performance Metrics")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Detailed metrics grid
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Create detailed metric labels
        self.detailed_metrics = {}
        detailed_metrics = [
            ("CPU Percent", "cpu_percent", "%"),
            ("Memory MB", "memory_mb", "MB"),
            ("Memory Percent", "memory_percent", "%"),
            ("Thread Count", "thread_count", ""),
            ("Events Processed", "events_processed", ""),
            ("Events/sec", "events_per_second", "/sec"),
            ("Queue Size", "queue_size", ""),
            ("Queue Utilization", "queue_utilization", "%"),
            ("Events Dropped", "events_dropped", ""),
            ("Drop Rate", "drop_rate", "%"),
            ("Processing Latency", "processing_latency_ms", "ms")
        ]
        
        for i, (label_text, key, unit) in enumerate(detailed_metrics):
            row = i // 2
            col = (i % 2) * 3
            
            label = QLabel(f"{label_text}:")
            value = QLabel("0")
            unit_label = QLabel(unit)
            
            self.detailed_metrics[key] = value
            
            metrics_layout.addWidget(label, row, col)
            metrics_layout.addWidget(value, row, col + 1)
            metrics_layout.addWidget(unit_label, row, col + 2)
        
        layout.addWidget(metrics_group)
        
        # Performance summary
        summary_group = QGroupBox("Performance Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        layout.addStretch()
        return widget
    
    def create_alerts_tab(self) -> QWidget:
        """Create the alerts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Performance Alerts")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Alert controls
        controls_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Alerts")
        clear_button.clicked.connect(self.clear_alerts)
        controls_layout.addWidget(clear_button)
        
        export_button = QPushButton("Export Alerts")
        export_button.clicked.connect(self.export_alerts)
        controls_layout.addWidget(export_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Alerts display
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        layout.addWidget(self.alerts_text)
        
        return widget
    
    def create_controls_tab(self) -> QWidget:
        """Create the controls tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Dashboard Controls")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Monitoring controls
        monitoring_group = QGroupBox("Monitoring Controls")
        monitoring_layout = QVBoxLayout(monitoring_group)
        
        # Refresh rate
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Refresh Rate (ms):"))
        self.refresh_spinbox = QSpinBox()
        self.refresh_spinbox.setRange(100, 10000)
        self.refresh_spinbox.setValue(1000)
        self.refresh_spinbox.valueChanged.connect(self.update_refresh_rate)
        refresh_layout.addWidget(self.refresh_spinbox)
        refresh_layout.addStretch()
        monitoring_layout.addLayout(refresh_layout)
        
        # Auto-scroll
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll alerts")
        self.auto_scroll_checkbox.setChecked(True)
        monitoring_layout.addWidget(self.auto_scroll_checkbox)
        
        layout.addWidget(monitoring_group)
        
        # Data export
        export_group = QGroupBox("Data Export")
        export_layout = QVBoxLayout(export_group)
        
        export_json_button = QPushButton("Export Performance Data (JSON)")
        export_json_button.clicked.connect(lambda: self.export_data('json'))
        export_layout.addWidget(export_json_button)
        
        export_csv_button = QPushButton("Export Performance Data (CSV)")
        export_csv_button.clicked.connect(lambda: self.export_data('csv'))
        export_layout.addWidget(export_csv_button)
        
        layout.addWidget(export_group)
        
        # Performance monitor controls
        monitor_group = QGroupBox("Performance Monitor")
        monitor_layout = QVBoxLayout(monitor_group)
        
        self.monitor_status_label = QLabel("Status: Active")
        monitor_layout.addWidget(self.monitor_status_label)
        
        clear_history_button = QPushButton("Clear History")
        clear_history_button.clicked.connect(self.clear_history)
        monitor_layout.addWidget(clear_history_button)
        
        layout.addWidget(monitor_group)
        
        layout.addStretch()
        return widget
    
    def setup_connections(self):
        """Setup signal connections."""
        pass  # Connections are set up in individual methods
    
    def setup_styling(self):
        """Setup the styling for the dashboard."""
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
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
                background-color: #404040;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                color: #ffffff;
            }
            QSpinBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def update_display(self):
        """Update the display with current performance data."""
        snapshot = self.performance_monitor.get_current_metrics()
        if not snapshot:
            return
        
        # Update overview metrics
        self.cpu_progress.setValue(int(snapshot.cpu_percent))
        self.cpu_value.setText(f"{snapshot.cpu_percent:.1f}%")
        
        self.memory_progress.setValue(int(snapshot.memory_mb))
        self.memory_value.setText(f"{snapshot.memory_mb:.1f} MB")
        
        self.events_progress.setValue(int(snapshot.events_per_second))
        self.events_value.setText(f"{int(snapshot.events_per_second)}")
        
        self.queue_progress.setValue(snapshot.queue_size)
        self.queue_value.setText(str(snapshot.queue_size))
        
        # Update performance targets status
        self.update_targets_status(snapshot)
        
        # Update uptime
        uptime_str = self.format_uptime(snapshot.uptime_seconds)
        self.uptime_label.setText(f"Uptime: {uptime_str}")
        
        # Update detailed metrics
        self.update_detailed_metrics(snapshot)
        
        # Update performance summary
        self.update_performance_summary()
    
    def update_targets_status(self, snapshot: PerformanceSnapshot):
        """Update the performance targets status indicators."""
        targets = self.performance_monitor.targets
        
        # CPU target
        cpu_met = snapshot.cpu_percent < targets['cpu_percent']
        self.targets_status['cpu_target'].setStyleSheet(
            f"color: {'green' if cpu_met else 'red'}; font-size: 20px;"
        )
        
        # Memory target
        memory_met = snapshot.memory_mb < targets['memory_mb']
        self.targets_status['memory_target'].setStyleSheet(
            f"color: {'green' if memory_met else 'red'}; font-size: 20px;"
        )
        
        # Events target
        events_met = snapshot.events_per_second > targets['events_per_second']
        self.targets_status['events_target'].setStyleSheet(
            f"color: {'green' if events_met else 'red'}; font-size: 20px;"
        )
        
        # Drop rate target
        drop_met = snapshot.drop_rate < targets['drop_rate']
        self.targets_status['drop_target'].setStyleSheet(
            f"color: {'green' if drop_met else 'red'}; font-size: 20px;"
        )
    
    def update_detailed_metrics(self, snapshot: PerformanceSnapshot):
        """Update the detailed metrics display."""
        metrics = [
            ('cpu_percent', f"{snapshot.cpu_percent:.2f}"),
            ('memory_mb', f"{snapshot.memory_mb:.2f}"),
            ('memory_percent', f"{snapshot.memory_percent:.2f}"),
            ('thread_count', str(snapshot.thread_count)),
            ('events_processed', str(snapshot.events_processed)),
            ('events_per_second', f"{snapshot.events_per_second:.2f}"),
            ('queue_size', str(snapshot.queue_size)),
            ('queue_utilization', f"{snapshot.queue_utilization:.2f}"),
            ('events_dropped', str(snapshot.events_dropped)),
            ('drop_rate', f"{snapshot.drop_rate:.2f}"),
            ('processing_latency_ms', f"{snapshot.processing_latency_ms:.2f}")
        ]
        
        for key, value in metrics:
            if key in self.detailed_metrics:
                self.detailed_metrics[key].setText(value)
    
    def update_performance_summary(self):
        """Update the performance summary text."""
        summary = self.performance_monitor.get_performance_summary(duration_minutes=5)
        if not summary:
            return
        
        summary_text = f"""
Performance Summary (Last {summary['duration_minutes']} minutes):
- Snapshots Analyzed: {summary['snapshots_analyzed']}

CPU Usage:
  Current: {summary['cpu_percent']['current']:.2f}% (Target: <{summary['cpu_percent']['target']}%)
  Average: {summary['cpu_percent']['average']:.2f}%
  Range: {summary['cpu_percent']['min']:.2f}% - {summary['cpu_percent']['max']:.2f}%

Memory Usage:
  Current: {summary['memory_mb']['current']:.2f} MB (Target: <{summary['memory_mb']['target']} MB)
  Average: {summary['memory_mb']['average']:.2f} MB
  Range: {summary['memory_mb']['min']:.2f} - {summary['memory_mb']['max']:.2f} MB

Events per Second:
  Current: {summary['events_per_second']['current']:.2f} (Target: >{summary['events_per_second']['target']})
  Average: {summary['events_per_second']['average']:.2f}
  Range: {summary['events_per_second']['min']:.2f} - {summary['events_per_second']['max']:.2f}

Targets Met:
  CPU: {'✓' if summary['targets_met']['cpu'] else '✗'}
  Memory: {'✓' if summary['targets_met']['memory'] else '✗'}
  Events: {'✓' if summary['targets_met']['events'] else '✗'}
        """
        
        self.summary_text.setPlainText(summary_text.strip())
    
    def on_alert(self, alert: PerformanceAlert):
        """Handle performance alerts."""
        self.alert_count += 1
        
        # Add to alerts display
        alert_text = f"[{self.format_timestamp(alert.timestamp)}] {alert.severity.upper()}: {alert.message}\n"
        self.alerts_text.append(alert_text)
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            self.alerts_text.moveCursor(self.alerts_text.textCursor().End)
        
        # Update status bar
        self.statusBar().showMessage(f"Alert #{self.alert_count}: {alert.message}")
        
        # Show critical alerts in message box
        if alert.severity == 'critical':
            QMessageBox.critical(self, "Critical Performance Alert", alert.message)
    
    def update_refresh_rate(self, rate: int):
        """Update the refresh rate."""
        self.update_timer.setInterval(rate)
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts_text.clear()
        self.alert_count = 0
        self.statusBar().showMessage("Alerts cleared")
    
    def export_alerts(self):
        """Export alerts to a file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Alerts", "alerts.txt", "Text Files (*.txt)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.alerts_text.toPlainText())
                QMessageBox.information(self, "Export Successful", f"Alerts exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export alerts: {e}")
    
    def export_data(self, format: str):
        """Export performance data."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Export Performance Data ({format.upper()})", 
            f"performance_data.{format}", f"{format.upper()} Files (*.{format})"
        )
        
        if filepath:
            if self.performance_monitor.export_data(filepath, format):
                QMessageBox.information(self, "Export Successful", f"Data exported to {filepath}")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export performance data")
    
    def clear_history(self):
        """Clear performance history."""
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all performance history?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.performance_monitor.clear_history()
            QMessageBox.information(self, "History Cleared", "Performance history has been cleared")
    
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display."""
        return time.strftime("%H:%M:%S", time.localtime(timestamp))
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.update_timer.stop()
        event.accept()


# Example usage
if __name__ == "__main__":
    # Create performance monitor
    monitor = PerformanceMonitor(monitoring_interval=1.0, enable_alerts=True)
    
    # Start monitoring
    if monitor.start():
        # Create and show dashboard
        app = QApplication(sys.argv)
        dashboard = PerformanceDashboard(monitor)
        dashboard.show()
        
        # Run the application
        sys.exit(app.exec_())
    else:
        print("Failed to start performance monitoring")
