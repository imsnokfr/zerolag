"""
Feedback Dashboard for ZeroLag

This module provides a GUI dashboard for monitoring user feedback,
issues, and community engagement.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QTabWidget, QTextEdit, QComboBox, QLineEdit,
                            QGroupBox, QGridLayout, QProgressBar, QSplitter,
                            QHeaderView, QMessageBox, QDialog, QFormLayout,
                            QSpinBox, QCheckBox, QDateEdit, QCalendarWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QDate
from PyQt5.QtGui import QFont, QIcon, QPixmap
from datetime import datetime, timedelta
import json

from src.core.feedback.feedback_manager import FeedbackManager, FeedbackEntry


class FeedbackDashboard(QWidget):
    """Main feedback dashboard widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.feedback_manager = FeedbackManager()
        self.setup_ui()
        self.setup_timer()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("ZeroLag Feedback Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("ZeroLag Feedback Dashboard")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        header_layout.addWidget(self.export_btn)
        
        main_layout.addLayout(header_layout)
        
        # Stats overview
        self.create_stats_overview(main_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Feedback list
        self.create_feedback_list(content_splitter)
        
        # Right panel - Details and actions
        self.create_details_panel(content_splitter)
        
        content_splitter.setSizes([600, 400])
        main_layout.addWidget(content_splitter)
        
        self.setLayout(main_layout)
    
    def create_stats_overview(self, parent_layout):
        """Create statistics overview section."""
        stats_group = QGroupBox("Statistics Overview")
        stats_layout = QHBoxLayout()
        
        # Total feedback
        self.total_feedback_label = QLabel("Total Feedback: 0")
        self.total_feedback_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_feedback_label)
        
        # Resolution rate
        self.resolution_rate_label = QLabel("Resolution Rate: 0%")
        self.resolution_rate_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.resolution_rate_label)
        
        # Average rating
        self.avg_rating_label = QLabel("Average Rating: 0.0/5.0")
        self.avg_rating_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.avg_rating_label)
        
        # Recent feedback count
        self.recent_feedback_label = QLabel("Recent (24h): 0")
        self.recent_feedback_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.recent_feedback_label)
        
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        parent_layout.addWidget(stats_group)
    
    def create_feedback_list(self, parent):
        """Create feedback list widget."""
        feedback_widget = QWidget()
        feedback_layout = QVBoxLayout()
        
        # Filters
        filters_layout = QHBoxLayout()
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "bug_report", "feature_request", "general_feedback", "performance_issue"])
        self.type_filter.currentTextChanged.connect(self.filter_feedback)
        filters_layout.addWidget(QLabel("Type:"))
        filters_layout.addWidget(self.type_filter)
        
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All Severities", "low", "medium", "high", "critical"])
        self.severity_filter.currentTextChanged.connect(self.filter_feedback)
        filters_layout.addWidget(QLabel("Severity:"))
        filters_layout.addWidget(self.severity_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "new", "in_progress", "resolved", "closed"])
        self.status_filter.currentTextChanged.connect(self.filter_feedback)
        filters_layout.addWidget(QLabel("Status:"))
        filters_layout.addWidget(self.status_filter)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search feedback...")
        self.search_box.textChanged.connect(self.filter_feedback)
        filters_layout.addWidget(QLabel("Search:"))
        filters_layout.addWidget(self.search_box)
        
        filters_layout.addStretch()
        feedback_layout.addLayout(filters_layout)
        
        # Feedback table
        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(6)
        self.feedback_table.setHorizontalHeaderLabels([
            "ID", "Type", "Title", "Severity", "Status", "Date"
        ])
        
        # Set column widths
        header = self.feedback_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Title
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Severity
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Date
        
        self.feedback_table.itemSelectionChanged.connect(self.on_feedback_selected)
        feedback_layout.addWidget(self.feedback_table)
        
        feedback_widget.setLayout(feedback_layout)
        parent.addWidget(feedback_widget)
    
    def create_details_panel(self, parent):
        """Create details panel widget."""
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        # Feedback details
        details_group = QGroupBox("Feedback Details")
        details_group_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_group_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_group_layout)
        details_layout.addWidget(details_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        self.update_status_btn = QPushButton("Update Status")
        self.update_status_btn.clicked.connect(self.update_feedback_status)
        self.update_status_btn.setEnabled(False)
        actions_layout.addWidget(self.update_status_btn)
        
        self.assign_btn = QPushButton("Assign to Developer")
        self.assign_btn.clicked.connect(self.assign_feedback)
        self.assign_btn.setEnabled(False)
        actions_layout.addWidget(self.assign_btn)
        
        self.resolve_btn = QPushButton("Mark as Resolved")
        self.resolve_btn.clicked.connect(self.resolve_feedback)
        self.resolve_btn.setEnabled(False)
        actions_layout.addWidget(self.resolve_btn)
        
        actions_group.setLayout(actions_layout)
        details_layout.addWidget(actions_group)
        
        # GitHub integration
        github_group = QGroupBox("GitHub Integration")
        github_layout = QVBoxLayout()
        
        self.github_status_label = QLabel("GitHub: Not Connected")
        github_layout.addWidget(self.github_status_label)
        
        self.sync_github_btn = QPushButton("Sync with GitHub")
        self.sync_github_btn.clicked.connect(self.sync_with_github)
        github_layout.addWidget(self.sync_github_btn)
        
        github_group.setLayout(github_layout)
        details_layout.addWidget(github_group)
        
        details_widget.setLayout(details_layout)
        parent.addWidget(details_widget)
    
    def setup_timer(self):
        """Setup auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def load_data(self):
        """Load feedback data."""
        self.feedback_manager.load_feedback()
        self.update_stats()
        self.populate_feedback_table()
    
    def update_stats(self):
        """Update statistics display."""
        stats = self.feedback_manager.get_feedback_stats()
        
        self.total_feedback_label.setText(f"Total Feedback: {stats.total_feedback}")
        self.resolution_rate_label.setText(f"Resolution Rate: {stats.resolution_rate:.1f}%")
        self.avg_rating_label.setText(f"Average Rating: {stats.average_rating:.1f}/5.0")
        
        # Count recent feedback (last 24 hours)
        recent_count = 0
        cutoff_time = datetime.now() - timedelta(hours=24)
        for entry in self.feedback_manager.feedback_entries:
            if datetime.fromtimestamp(entry.timestamp) > cutoff_time:
                recent_count += 1
        
        self.recent_feedback_label.setText(f"Recent (24h): {recent_count}")
    
    def populate_feedback_table(self):
        """Populate feedback table with data."""
        self.feedback_table.setRowCount(len(self.feedback_manager.feedback_entries))
        
        for row, entry in enumerate(self.feedback_manager.feedback_entries):
            self.feedback_table.setItem(row, 0, QTableWidgetItem(entry.feedback_id))
            self.feedback_table.setItem(row, 1, QTableWidgetItem(entry.feedback_type))
            self.feedback_table.setItem(row, 2, QTableWidgetItem(entry.title))
            self.feedback_table.setItem(row, 3, QTableWidgetItem(entry.severity))
            self.feedback_table.setItem(row, 4, QTableWidgetItem(entry.status))
            self.feedback_table.setItem(row, 5, QTableWidgetItem(
                datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M')
            ))
    
    def filter_feedback(self):
        """Filter feedback based on current filters."""
        # This is a simplified implementation
        # In a real application, you would implement proper filtering
        self.populate_feedback_table()
    
    def on_feedback_selected(self):
        """Handle feedback selection."""
        current_row = self.feedback_table.currentRow()
        if current_row >= 0:
            feedback_id = self.feedback_table.item(current_row, 0).text()
            entry = self.feedback_manager.get_feedback(feedback_id)
            if entry:
                self.display_feedback_details(entry)
                self.update_status_btn.setEnabled(True)
                self.assign_btn.setEnabled(True)
                self.resolve_btn.setEnabled(True)
    
    def display_feedback_details(self, entry: FeedbackEntry):
        """Display feedback details."""
        details = f"""
Feedback ID: {entry.feedback_id}
Type: {entry.feedback_type}
Title: {entry.title}
Severity: {entry.severity}
Status: {entry.status}
Category: {entry.category}
User ID: {entry.user_id}
Date: {datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

Description:
{entry.description}

System Information:
{json.dumps(entry.system_info, indent=2)}

Tags: {', '.join(entry.tags) if entry.tags else 'None'}
Rating: {entry.user_rating if entry.user_rating else 'Not rated'}
Assigned to: {entry.assigned_to if entry.assigned_to else 'Unassigned'}

Resolution: {entry.resolution if entry.resolution else 'Not resolved'}
"""
        self.details_text.setPlainText(details)
    
    def update_feedback_status(self):
        """Update feedback status."""
        current_row = self.feedback_table.currentRow()
        if current_row >= 0:
            feedback_id = self.feedback_table.item(current_row, 0).text()
            # In a real implementation, you would show a dialog to select new status
            QMessageBox.information(self, "Update Status", f"Update status for {feedback_id}")
    
    def assign_feedback(self):
        """Assign feedback to developer."""
        current_row = self.feedback_table.currentRow()
        if current_row >= 0:
            feedback_id = self.feedback_table.item(current_row, 0).text()
            # In a real implementation, you would show a dialog to select developer
            QMessageBox.information(self, "Assign Feedback", f"Assign {feedback_id} to developer")
    
    def resolve_feedback(self):
        """Mark feedback as resolved."""
        current_row = self.feedback_table.currentRow()
        if current_row >= 0:
            feedback_id = self.feedback_table.item(current_row, 0).text()
            # In a real implementation, you would show a dialog to enter resolution
            QMessageBox.information(self, "Resolve Feedback", f"Resolve {feedback_id}")
    
    def sync_with_github(self):
        """Sync with GitHub issues."""
        QMessageBox.information(self, "GitHub Sync", "Syncing with GitHub issues...")
    
    def export_data(self):
        """Export feedback data."""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Feedback Data", "feedback_export.json", "JSON Files (*.json)"
        )
        
        if file_path:
            self.feedback_manager.export_feedback(file_path)
            QMessageBox.information(self, "Export Complete", f"Data exported to {file_path}")


def main():
    """Main function for testing the dashboard."""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dashboard = FeedbackDashboard()
    dashboard.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
