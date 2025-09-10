"""
Hotkey Configuration GUI for ZeroLag

This module provides a graphical user interface for configuring hotkeys,
including profile management, binding creation, and conflict resolution.

Features:
- Visual hotkey configuration
- Profile management interface
- Real-time conflict detection
- Hotkey testing and validation
- Import/export functionality
- Preset hotkey configurations
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QSlider, QMessageBox,
    QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QFormLayout, QListWidget,
    QListWidgetItem, QProgressBar, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon, QPixmap, QKeySequence

from .hotkey_config import (
    HotkeyConfigManager, HotkeyProfile, HotkeyBinding, HotkeyProfileType
)
from .hotkey_actions import HotkeyActionType
from .hotkey_detector import HotkeyModifier
from .hotkey_validator import HotkeyValidator, ValidationResult

logger = logging.getLogger(__name__)

class HotkeyConfigMode(Enum):
    """Configuration modes for the hotkey GUI."""
    VIEW = "view"
    EDIT = "edit"
    TEST = "test"

@dataclass
class HotkeyConfigGUISettings:
    """Settings for the hotkey configuration GUI."""
    auto_save: bool = True
    auto_save_interval: float = 30.0  # seconds
    show_conflicts: bool = True
    enable_hotkey_testing: bool = True
    theme: str = "dark"
    font_size: int = 10
    window_width: int = 1000
    window_height: int = 700

class HotkeyBindingWidget(QWidget):
    """Widget for displaying and editing a single hotkey binding."""
    
    binding_changed = pyqtSignal(int, dict)  # hotkey_id, changes
    binding_removed = pyqtSignal(int)  # hotkey_id
    
    def __init__(self, binding: HotkeyBinding, parent=None):
        super().__init__(parent)
        self.binding = binding
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout()
        
        # Action type
        self.action_combo = QComboBox()
        for action_type in HotkeyActionType:
            self.action_combo.addItem(action_type.value, action_type)
        self.action_combo.setCurrentText(self.binding.action_type.value)
        layout.addWidget(QLabel("Action:"))
        layout.addWidget(self.action_combo)
        
        # Key combination display
        self.key_label = QLabel(self._format_key_combination())
        self.key_label.setStyleSheet("background-color: #2b2b2b; padding: 5px; border: 1px solid #555;")
        layout.addWidget(QLabel("Key:"))
        layout.addWidget(self.key_label)
        
        # Description
        self.description_edit = QLineEdit(self.binding.description)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_edit)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(self.binding.enabled)
        layout.addWidget(self.enabled_checkbox)
        
        # Buttons
        self.edit_button = QPushButton("Edit")
        self.test_button = QPushButton("Test")
        self.remove_button = QPushButton("Remove")
        
        layout.addWidget(self.edit_button)
        layout.addWidget(self.test_button)
        layout.addWidget(self.remove_button)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.action_combo.currentTextChanged.connect(self._on_action_changed)
        self.description_edit.textChanged.connect(self._on_description_changed)
        self.enabled_checkbox.toggled.connect(self._on_enabled_changed)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.test_button.clicked.connect(self._on_test_clicked)
        self.remove_button.clicked.connect(self._on_remove_clicked)
    
    def _format_key_combination(self) -> str:
        """Format the key combination for display."""
        modifiers = []
        if self.binding.modifiers & HotkeyModifier.CTRL:
            modifiers.append("Ctrl")
        if self.binding.modifiers & HotkeyModifier.ALT:
            modifiers.append("Alt")
        if self.binding.modifiers & HotkeyModifier.SHIFT:
            modifiers.append("Shift")
        if self.binding.modifiers & HotkeyModifier.WIN:
            modifiers.append("Win")
        
        if modifiers:
            return "+".join(modifiers) + "+" + self.binding.key_name
        return self.binding.key_name
    
    def _on_action_changed(self, text: str):
        """Handle action type change."""
        action_type = HotkeyActionType(text)
        self.binding.action_type = action_type
        self._emit_changes()
    
    def _on_description_changed(self, text: str):
        """Handle description change."""
        self.binding.description = text
        self._emit_changes()
    
    def _on_enabled_changed(self, checked: bool):
        """Handle enabled state change."""
        self.binding.enabled = checked
        self._emit_changes()
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        # Open key capture dialog
        dialog = KeyCaptureDialog(self.binding, self)
        if dialog.exec_() == QDialog.Accepted:
            new_binding = dialog.get_binding()
            if new_binding:
                self.binding = new_binding
                self.key_label.setText(self._format_key_combination())
                self._emit_changes()
    
    def _on_test_clicked(self):
        """Handle test button click."""
        # Emit test signal (will be handled by parent)
        pass
    
    def _on_remove_clicked(self):
        """Handle remove button click."""
        reply = QMessageBox.question(
            self, "Remove Binding",
            f"Are you sure you want to remove the binding for {self.binding.action_type.value}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.binding_removed.emit(self.binding.hotkey_id)
    
    def _emit_changes(self):
        """Emit binding changed signal."""
        changes = {
            'action_type': self.binding.action_type,
            'description': self.binding.description,
            'enabled': self.binding.enabled
        }
        self.binding_changed.emit(self.binding.hotkey_id, changes)

class KeyCaptureDialog(QDialog):
    """Dialog for capturing key combinations."""
    
    def __init__(self, binding: HotkeyBinding, parent=None):
        super().__init__(parent)
        self.binding = binding
        self.captured_modifiers = 0
        self.captured_key = 0
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Capture Key Combination")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Press the key combination you want to use for this action.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Key display
        self.key_display = QLabel("Press keys...")
        self.key_display.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: white;
                padding: 20px;
                border: 2px solid #555;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.key_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.key_display)
        
        # Current binding info
        current_info = QLabel(f"Current: {self._format_binding(self.binding)}")
        current_info.setStyleSheet("color: #888;")
        layout.addWidget(current_info)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Connect buttons
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
    
    def setup_connections(self):
        """Set up signal connections."""
        # Enable key capture
        self.setFocusPolicy(Qt.StrongFocus)
        self.keyPressEvent = self._on_key_press
        self.keyReleaseEvent = self._on_key_release
    
    def _on_key_press(self, event):
        """Handle key press events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Convert Qt modifiers to our format
        captured_modifiers = 0
        if modifiers & Qt.ControlModifier:
            captured_modifiers |= HotkeyModifier.CTRL
        if modifiers & Qt.AltModifier:
            captured_modifiers |= HotkeyModifier.ALT
        if modifiers & Qt.ShiftModifier:
            captured_modifiers |= HotkeyModifier.SHIFT
        if modifiers & Qt.MetaModifier:
            captured_modifiers |= HotkeyModifier.WIN
        
        self.captured_modifiers = captured_modifiers
        self.captured_key = key
        
        # Update display
        self._update_display()
    
    def _on_key_release(self, event):
        """Handle key release events."""
        pass
    
    def _update_display(self):
        """Update the key display."""
        if self.captured_key:
            key_name = QKeySequence(self.captured_key).toString()
            modifiers = []
            
            if self.captured_modifiers & HotkeyModifier.CTRL:
                modifiers.append("Ctrl")
            if self.captured_modifiers & HotkeyModifier.ALT:
                modifiers.append("Alt")
            if self.captured_modifiers & HotkeyModifier.SHIFT:
                modifiers.append("Shift")
            if self.captured_modifiers & HotkeyModifier.WIN:
                modifiers.append("Win")
            
            if modifiers:
                display_text = "+".join(modifiers) + "+" + key_name
            else:
                display_text = key_name
            
            self.key_display.setText(display_text)
    
    def _format_binding(self, binding: HotkeyBinding) -> str:
        """Format a binding for display."""
        modifiers = []
        if binding.modifiers & HotkeyModifier.CTRL:
            modifiers.append("Ctrl")
        if binding.modifiers & HotkeyModifier.ALT:
            modifiers.append("Alt")
        if binding.modifiers & HotkeyModifier.SHIFT:
            modifiers.append("Shift")
        if binding.modifiers & HotkeyModifier.WIN:
            modifiers.append("Win")
        
        if modifiers:
            return "+".join(modifiers) + "+" + binding.key_name
        return binding.key_name
    
    def get_binding(self) -> Optional[HotkeyBinding]:
        """Get the captured binding."""
        if self.captured_key:
            # Convert Qt key to virtual key (simplified)
            virtual_key = self.captured_key
            key_name = QKeySequence(self.captured_key).toString()
            
            return HotkeyBinding(
                hotkey_id=self.binding.hotkey_id,
                action_type=self.binding.action_type,
                modifiers=self.captured_modifiers,
                virtual_key=virtual_key,
                key_name=key_name,
                description=self.binding.description,
                enabled=self.binding.enabled,
                created_at=self.binding.created_at,
                modified_at=time.time(),
                user_data=self.binding.user_data
            )
        return None

class HotkeyConfigGUI(QWidget):
    """Main GUI for hotkey configuration."""
    
    config_changed = pyqtSignal()
    
    def __init__(self, config_manager: HotkeyConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = HotkeyConfigGUISettings()
        self.validator = HotkeyValidator()
        self.current_profile = None
        self.binding_widgets = {}
        
        self.setup_ui()
        self.setup_connections()
        self.load_current_profile()
        
        # Auto-save timer
        if self.settings.auto_save:
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(int(self.settings.auto_save_interval * 1000))
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("ZeroLag Hotkey Configuration")
        self.resize(self.settings.window_width, self.settings.window_height)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Profile management
        left_panel = self.create_profile_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Binding management
        right_panel = self.create_binding_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([300, 700])
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
    
    def create_toolbar(self) -> QWidget:
        """Create the toolbar."""
        toolbar = QWidget()
        layout = QHBoxLayout()
        
        # Profile controls
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(200)
        layout.addWidget(QLabel("Profile:"))
        layout.addWidget(self.profile_combo)
        
        self.new_profile_btn = QPushButton("New Profile")
        self.import_profile_btn = QPushButton("Import")
        self.export_profile_btn = QPushButton("Export")
        
        layout.addWidget(self.new_profile_btn)
        layout.addWidget(self.import_profile_btn)
        layout.addWidget(self.export_profile_btn)
        
        layout.addStretch()
        
        # Global controls
        self.save_btn = QPushButton("Save")
        self.reload_btn = QPushButton("Reload")
        self.test_all_btn = QPushButton("Test All")
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.reload_btn)
        layout.addWidget(self.test_all_btn)
        
        toolbar.setLayout(layout)
        return toolbar
    
    def create_profile_panel(self) -> QWidget:
        """Create the profile management panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Profile info
        info_group = QGroupBox("Profile Information")
        info_layout = QFormLayout()
        
        self.profile_name_edit = QLineEdit()
        self.profile_type_combo = QComboBox()
        for profile_type in HotkeyProfileType:
            self.profile_type_combo.addItem(profile_type.value, profile_type)
        
        self.profile_description_edit = QTextEdit()
        self.profile_description_edit.setMaximumHeight(100)
        
        info_layout.addRow("Name:", self.profile_name_edit)
        info_layout.addRow("Type:", self.profile_type_combo)
        info_layout.addRow("Description:", self.profile_description_edit)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Profile actions
        actions_group = QGroupBox("Profile Actions")
        actions_layout = QVBoxLayout()
        
        self.duplicate_profile_btn = QPushButton("Duplicate Profile")
        self.delete_profile_btn = QPushButton("Delete Profile")
        self.reset_profile_btn = QPushButton("Reset to Defaults")
        
        actions_layout.addWidget(self.duplicate_profile_btn)
        actions_layout.addWidget(self.delete_profile_btn)
        actions_layout.addWidget(self.reset_profile_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Profile statistics
        stats_group = QGroupBox("Profile Statistics")
        stats_layout = QFormLayout()
        
        self.binding_count_label = QLabel("0")
        self.conflict_count_label = QLabel("0")
        self.last_modified_label = QLabel("Never")
        
        stats_layout.addRow("Bindings:", self.binding_count_label)
        stats_layout.addRow("Conflicts:", self.conflict_count_label)
        stats_layout.addRow("Last Modified:", self.last_modified_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_binding_panel(self) -> QWidget:
        """Create the binding management panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Binding controls
        controls_layout = QHBoxLayout()
        
        self.add_binding_btn = QPushButton("Add Binding")
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.clear_all_btn = QPushButton("Clear All")
        
        controls_layout.addWidget(self.add_binding_btn)
        controls_layout.addWidget(self.remove_selected_btn)
        controls_layout.addWidget(self.clear_all_btn)
        
        controls_layout.addStretch()
        
        # Filter controls
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter bindings...")
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.filter_edit)
        
        layout.addLayout(controls_layout)
        
        # Binding list
        self.binding_scroll = QWidget()
        self.binding_layout = QVBoxLayout()
        self.binding_scroll.setLayout(self.binding_layout)
        
        layout.addWidget(self.binding_scroll)
        
        panel.setLayout(layout)
        return panel
    
    def setup_connections(self):
        """Set up signal connections."""
        # Profile controls
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        self.profile_name_edit.textChanged.connect(self.on_profile_name_changed)
        self.profile_type_combo.currentTextChanged.connect(self.on_profile_type_changed)
        self.profile_description_edit.textChanged.connect(self.on_profile_description_changed)
        
        # Profile actions
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        self.duplicate_profile_btn.clicked.connect(self.duplicate_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.reset_profile_btn.clicked.connect(self.reset_profile)
        self.import_profile_btn.clicked.connect(self.import_profile)
        self.export_profile_btn.clicked.connect(self.export_profile)
        
        # Global controls
        self.save_btn.clicked.connect(self.save_config)
        self.reload_btn.clicked.connect(self.reload_config)
        self.test_all_btn.clicked.connect(self.test_all_bindings)
        
        # Binding controls
        self.add_binding_btn.clicked.connect(self.add_binding)
        self.remove_selected_btn.clicked.connect(self.remove_selected_bindings)
        self.clear_all_btn.clicked.connect(self.clear_all_bindings)
        self.filter_edit.textChanged.connect(self.filter_bindings)
    
    def load_current_profile(self):
        """Load the current profile."""
        profile_names = self.config_manager.get_profile_list()
        self.profile_combo.clear()
        self.profile_combo.addItems(profile_names)
        
        if profile_names:
            active_profile = self.config_manager.get_active_profile()
            if active_profile:
                self.profile_combo.setCurrentText(active_profile.name)
                self.current_profile = active_profile
                self.update_profile_info()
                self.update_binding_list()
    
    def update_profile_info(self):
        """Update profile information display."""
        if not self.current_profile:
            return
        
        self.profile_name_edit.setText(self.current_profile.name)
        self.profile_type_combo.setCurrentText(self.current_profile.profile_type.value)
        self.profile_description_edit.setPlainText(self.current_profile.description)
        
        # Update statistics
        self.binding_count_label.setText(str(len(self.current_profile.bindings)))
        
        # Check for conflicts
        conflicts = self.validator.check_conflicts(self.current_profile.bindings.values())
        self.conflict_count_label.setText(str(len(conflicts)))
        
        # Update last modified
        import datetime
        last_modified = datetime.datetime.fromtimestamp(self.current_profile.modified_at)
        self.last_modified_label.setText(last_modified.strftime("%Y-%m-%d %H:%M:%S"))
    
    def update_binding_list(self):
        """Update the binding list display."""
        # Clear existing widgets
        for widget in self.binding_widgets.values():
            widget.deleteLater()
        self.binding_widgets.clear()
        
        if not self.current_profile:
            return
        
        # Add binding widgets
        for binding in self.current_profile.bindings.values():
            widget = HotkeyBindingWidget(binding)
            widget.binding_changed.connect(self.on_binding_changed)
            widget.binding_removed.connect(self.on_binding_removed)
            
            self.binding_layout.addWidget(widget)
            self.binding_widgets[binding.hotkey_id] = widget
    
    def on_profile_changed(self, profile_name: str):
        """Handle profile change."""
        if profile_name in self.config_manager.config.profiles:
            self.current_profile = self.config_manager.config.profiles[profile_name]
            self.config_manager.set_active_profile(profile_name)
            self.update_profile_info()
            self.update_binding_list()
    
    def on_profile_name_changed(self, name: str):
        """Handle profile name change."""
        if self.current_profile and name != self.current_profile.name:
            # Check for name conflicts
            if name in self.config_manager.config.profiles:
                QMessageBox.warning(self, "Name Conflict", f"Profile '{name}' already exists.")
                self.profile_name_edit.setText(self.current_profile.name)
                return
            
            # Update profile name
            old_name = self.current_profile.name
            self.current_profile.name = name
            
            # Update in config
            self.config_manager.config.profiles[name] = self.current_profile
            del self.config_manager.config.profiles[old_name]
            
            # Update combo box
            self.profile_combo.setItemText(self.profile_combo.currentIndex(), name)
    
    def on_profile_type_changed(self, profile_type: str):
        """Handle profile type change."""
        if self.current_profile:
            self.current_profile.profile_type = HotkeyProfileType(profile_type)
    
    def on_profile_description_changed(self):
        """Handle profile description change."""
        if self.current_profile:
            self.current_profile.description = self.profile_description_edit.toPlainText()
    
    def create_new_profile(self):
        """Create a new profile."""
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name:
            try:
                profile = self.config_manager.create_profile(name)
                self.profile_combo.addItem(name)
                self.profile_combo.setCurrentText(name)
                self.current_profile = profile
                self.update_profile_info()
                self.update_binding_list()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def duplicate_profile(self):
        """Duplicate the current profile."""
        if not self.current_profile:
            return
        
        name, ok = QInputDialog.getText(self, "Duplicate Profile", "New profile name:")
        if ok and name:
            try:
                # Create new profile
                new_profile = HotkeyProfile(
                    name=name,
                    profile_type=self.current_profile.profile_type,
                    description=f"Copy of {self.current_profile.description}",
                    bindings=self.current_profile.bindings.copy()
                )
                
                self.config_manager.config.profiles[name] = new_profile
                self.profile_combo.addItem(name)
                self.profile_combo.setCurrentText(name)
                self.current_profile = new_profile
                self.update_profile_info()
                self.update_binding_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def delete_profile(self):
        """Delete the current profile."""
        if not self.current_profile:
            return
        
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Are you sure you want to delete profile '{self.current_profile.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.config_manager.delete_profile(self.current_profile.name):
                self.profile_combo.removeItem(self.profile_combo.currentIndex())
                self.current_profile = None
                self.update_profile_info()
                self.update_binding_list()
    
    def reset_profile(self):
        """Reset profile to defaults."""
        if not self.current_profile:
            return
        
        reply = QMessageBox.question(
            self, "Reset Profile",
            f"Are you sure you want to reset profile '{self.current_profile.name}' to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear all bindings
            self.current_profile.bindings.clear()
            self.update_binding_list()
            self.update_profile_info()
    
    def import_profile(self):
        """Import a profile from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile", "", "JSON Files (*.json)"
        )
        
        if file_path:
            if self.config_manager.import_profile(file_path):
                self.load_current_profile()
                QMessageBox.information(self, "Success", "Profile imported successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to import profile.")
    
    def export_profile(self):
        """Export the current profile."""
        if not self.current_profile:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile", f"{self.current_profile.name}.json", "JSON Files (*.json)"
        )
        
        if file_path:
            if self.config_manager.export_profile(self.current_profile.name, file_path):
                QMessageBox.information(self, "Success", "Profile exported successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to export profile.")
    
    def add_binding(self):
        """Add a new binding."""
        if not self.current_profile:
            return
        
        # Create a new binding with default values
        binding = HotkeyBinding(
            hotkey_id=self.config_manager.next_hotkey_id,
            action_type=HotkeyActionType.TOGGLE_ZEROLAG,
            modifiers=HotkeyModifier.CTRL | HotkeyModifier.ALT,
            virtual_key=90,  # Z key
            key_name="Z",
            description="New binding"
        )
        
        # Add to profile
        self.current_profile.bindings[binding.hotkey_id] = binding
        self.config_manager.next_hotkey_id += 1
        
        # Update display
        self.update_binding_list()
        self.update_profile_info()
    
    def remove_selected_bindings(self):
        """Remove selected bindings."""
        # This would be implemented with selection tracking
        pass
    
    def clear_all_bindings(self):
        """Clear all bindings."""
        if not self.current_profile:
            return
        
        reply = QMessageBox.question(
            self, "Clear All Bindings",
            "Are you sure you want to clear all bindings?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_profile.bindings.clear()
            self.update_binding_list()
            self.update_profile_info()
    
    def filter_bindings(self, text: str):
        """Filter bindings based on text."""
        for widget in self.binding_widgets.values():
            if text.lower() in widget.binding.action_type.value.lower() or \
               text.lower() in widget.binding.description.lower():
                widget.show()
            else:
                widget.hide()
    
    def on_binding_changed(self, hotkey_id: int, changes: dict):
        """Handle binding changes."""
        if self.current_profile and hotkey_id in self.current_profile.bindings:
            binding = self.current_profile.bindings[hotkey_id]
            for key, value in changes.items():
                setattr(binding, key, value)
            binding.modified_at = time.time()
            self.current_profile.modified_at = time.time()
            self.update_profile_info()
    
    def on_binding_removed(self, hotkey_id: int):
        """Handle binding removal."""
        if self.current_profile and hotkey_id in self.current_profile.bindings:
            del self.current_profile.bindings[hotkey_id]
            self.update_binding_list()
            self.update_profile_info()
    
    def save_config(self):
        """Save the configuration."""
        if self.config_manager.save_config():
            self.status_bar.showMessage("Configuration saved successfully.")
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "Error", "Failed to save configuration.")
    
    def reload_config(self):
        """Reload the configuration."""
        if self.config_manager.load_config():
            self.load_current_profile()
            self.status_bar.showMessage("Configuration reloaded successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to reload configuration.")
    
    def test_all_bindings(self):
        """Test all bindings."""
        # This would implement hotkey testing functionality
        QMessageBox.information(self, "Test All", "Testing all bindings...")
    
    def auto_save(self):
        """Auto-save the configuration."""
        if self.settings.auto_save:
            self.save_config()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.settings.auto_save:
            self.save_config()
        event.accept()

# Missing import for QInputDialog
from PyQt5.QtWidgets import QInputDialog
