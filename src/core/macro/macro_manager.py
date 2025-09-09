"""
Macro Manager for ZeroLag

This module implements comprehensive macro management functionality including:
- Macro library management and organization
- Profile-based macro storage
- Macro sharing and import/export
- Search and filtering capabilities
- Version control and backup
- Performance monitoring and optimization
- Integration with input handlers

Features:
- Centralized macro management
- Profile-based organization
- Search and filtering
- Import/export functionality
- Version control
- Performance monitoring
- Integration with all macro components
"""

import time
import json
import os
import shutil
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import hashlib
import zipfile
from pathlib import Path

from .macro_recorder import MacroRecording, MacroRecorder, MacroRecorderConfig
from .macro_player import MacroPlayer, PlaybackConfig
from .macro_editor import MacroEditor, EditorConfig


class MacroCategory(Enum):
    """Macro categories for organization."""
    GAMING = "gaming"
    PRODUCTIVITY = "productivity"
    AUTOMATION = "automation"
    TESTING = "testing"
    CUSTOM = "custom"


class MacroStatus(Enum):
    """Macro status indicators."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RECORDING = "recording"
    PLAYING = "playing"
    EDITING = "editing"
    ERROR = "error"


@dataclass
class MacroProfile:
    """Macro profile for organization."""
    name: str
    description: str = ""
    category: MacroCategory = MacroCategory.CUSTOM
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    macros: List[str] = field(default_factory=list)  # Macro names
    settings: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False


@dataclass
class MacroLibrary:
    """Macro library with metadata."""
    name: str
    description: str = ""
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    macros: Dict[str, MacroRecording] = field(default_factory=dict)
    profiles: Dict[str, MacroProfile] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    author: str = ""
    license: str = "MIT"


@dataclass
class MacroManagerConfig:
    """Configuration for macro manager."""
    enabled: bool = True
    storage_path: str = "macros"
    backup_enabled: bool = True
    backup_interval: float = 3600.0  # 1 hour
    max_backups: int = 10
    auto_save: bool = True
    auto_save_interval: float = 30.0
    compression_enabled: bool = True
    version_control: bool = True
    max_versions: int = 5
    search_enabled: bool = True
    indexing_enabled: bool = True


@dataclass
class MacroManagerStats:
    """Statistics for macro manager."""
    total_macros: int = 0
    total_profiles: int = 0
    total_libraries: int = 0
    active_recordings: int = 0
    active_playbacks: int = 0
    active_editors: int = 0
    storage_usage_mb: float = 0.0
    last_backup_time: float = 0.0
    last_index_time: float = 0.0
    search_queries: int = 0
    import_operations: int = 0
    export_operations: int = 0


class MacroManager:
    """
    Comprehensive macro management system for ZeroLag.
    
    Provides centralized management of macros, profiles, and libraries
    with advanced features like search, version control, and sharing.
    """
    
    def __init__(self, config: Optional[MacroManagerConfig] = None):
        """
        Initialize macro manager.
        
        Args:
            config: Manager configuration
        """
        self.config = config or MacroManagerConfig()
        self.libraries: Dict[str, MacroLibrary] = {}
        self.current_profile: Optional[MacroProfile] = None
        self.active_recordings: Dict[str, MacroRecorder] = {}
        self.active_playbacks: Dict[str, MacroPlayer] = {}
        self.active_editors: Dict[str, MacroEditor] = {}
        
        # Statistics
        self.stats = MacroManagerStats()
        
        # Threading
        self.lock = threading.RLock()
        
        # Callbacks
        self.change_callbacks: List[Callable[[str, str], None]] = []  # (operation, macro_name)
        self.status_callbacks: List[Callable[[str, MacroStatus], None]] = []  # (macro_name, status)
        
        # Initialize storage
        self._initialize_storage()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_storage(self):
        """Initialize storage directory and load existing data."""
        try:
            # Create storage directory
            os.makedirs(self.config.storage_path, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['macros', 'profiles', 'libraries', 'backups', 'exports']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.config.storage_path, subdir), exist_ok=True)
            
            # Load existing data
            self._load_libraries()
            self._load_profiles()
            
        except Exception as e:
            logging.error(f"Error initializing storage: {e}")
    
    def _load_libraries(self):
        """Load existing macro libraries."""
        try:
            libraries_path = os.path.join(self.config.storage_path, 'libraries')
            for filename in os.listdir(libraries_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(libraries_path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        library = MacroLibrary(**data)
                        self.libraries[library.name] = library
                        
        except Exception as e:
            logging.error(f"Error loading libraries: {e}")
    
    def _load_profiles(self):
        """Load existing macro profiles."""
        try:
            profiles_path = os.path.join(self.config.storage_path, 'profiles')
            for filename in os.listdir(profiles_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(profiles_path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        profile = MacroProfile(**data)
                        if profile.is_default:
                            self.current_profile = profile
                        
        except Exception as e:
            logging.error(f"Error loading profiles: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks."""
        if self.config.backup_enabled:
            self._start_backup_timer()
        
        if self.config.auto_save:
            self._start_auto_save_timer()
    
    def _start_backup_timer(self):
        """Start backup timer."""
        def backup_task():
            while True:
                try:
                    time.sleep(self.config.backup_interval)
                    self._create_backup()
                except Exception as e:
                    logging.error(f"Error in backup task: {e}")
        
        backup_thread = threading.Thread(target=backup_task, daemon=True, name="MacroBackupThread")
        backup_thread.start()
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        def auto_save_task():
            while True:
                try:
                    time.sleep(self.config.auto_save_interval)
                    self._auto_save_all()
                except Exception as e:
                    logging.error(f"Error in auto-save task: {e}")
        
        auto_save_thread = threading.Thread(target=auto_save_task, daemon=True, name="MacroAutoSaveThread")
        auto_save_thread.start()
    
    def create_library(self, name: str, description: str = "", author: str = "", 
                      license: str = "MIT") -> bool:
        """
        Create a new macro library.
        
        Args:
            name: Library name
            description: Library description
            author: Library author
            license: Library license
            
        Returns:
            True if created successfully
        """
        try:
            with self.lock:
                if name in self.libraries:
                    return False
                
                library = MacroLibrary(
                    name=name,
                    description=description,
                    author=author,
                    license=license
                )
                
                self.libraries[name] = library
                self.stats.total_libraries += 1
                
                # Save library
                self._save_library(library)
                
                return True
                
        except Exception as e:
            logging.error(f"Error creating library: {e}")
            return False
    
    def delete_library(self, name: str) -> bool:
        """
        Delete a macro library.
        
        Args:
            name: Library name
            
        Returns:
            True if deleted successfully
        """
        try:
            with self.lock:
                if name not in self.libraries:
                    return False
                
                # Delete library file
                library_path = os.path.join(self.config.storage_path, 'libraries', f"{name}.json")
                if os.path.exists(library_path):
                    os.remove(library_path)
                
                # Remove from memory
                del self.libraries[name]
                self.stats.total_libraries -= 1
                
                return True
                
        except Exception as e:
            logging.error(f"Error deleting library: {e}")
            return False
    
    def add_macro_to_library(self, library_name: str, macro: MacroRecording) -> bool:
        """
        Add a macro to a library.
        
        Args:
            library_name: Target library name
            macro: Macro to add
            
        Returns:
            True if added successfully
        """
        try:
            with self.lock:
                if library_name not in self.libraries:
                    return False
                
                library = self.libraries[library_name]
                library.macros[macro.name] = macro
                library.modified_at = time.time()
                
                # Update statistics
                self.stats.total_macros += 1
                
                # Save library
                self._save_library(library)
                
                # Trigger callbacks
                self._trigger_change_callbacks("add_macro", macro.name)
                
                return True
                
        except Exception as e:
            logging.error(f"Error adding macro to library: {e}")
            return False
    
    def remove_macro_from_library(self, library_name: str, macro_name: str) -> bool:
        """
        Remove a macro from a library.
        
        Args:
            library_name: Library name
            macro_name: Macro name
            
        Returns:
            True if removed successfully
        """
        try:
            with self.lock:
                if library_name not in self.libraries:
                    return False
                
                library = self.libraries[library_name]
                if macro_name not in library.macros:
                    return False
                
                del library.macros[macro_name]
                library.modified_at = time.time()
                
                # Update statistics
                self.stats.total_macros -= 1
                
                # Save library
                self._save_library(library)
                
                # Trigger callbacks
                self._trigger_change_callbacks("remove_macro", macro_name)
                
                return True
                
        except Exception as e:
            logging.error(f"Error removing macro from library: {e}")
            return False
    
    def get_macro(self, library_name: str, macro_name: str) -> Optional[MacroRecording]:
        """
        Get a macro from a library.
        
        Args:
            library_name: Library name
            macro_name: Macro name
            
        Returns:
            Macro recording or None if not found
        """
        try:
            with self.lock:
                if library_name not in self.libraries:
                    return None
                
                library = self.libraries[library_name]
                return library.macros.get(macro_name)
                
        except Exception as e:
            logging.error(f"Error getting macro: {e}")
            return None
    
    def search_macros(self, query: str, library_name: Optional[str] = None, 
                     category: Optional[MacroCategory] = None) -> List[Tuple[str, str, MacroRecording]]:
        """
        Search for macros.
        
        Args:
            query: Search query
            library_name: Filter by library name
            category: Filter by category
            
        Returns:
            List of (library_name, macro_name, macro) tuples
        """
        try:
            results = []
            query_lower = query.lower()
            
            with self.lock:
                for lib_name, library in self.libraries.items():
                    if library_name and lib_name != library_name:
                        continue
                    
                    for macro_name, macro in library.macros.items():
                        # Check name match
                        if query_lower in macro_name.lower():
                            results.append((lib_name, macro_name, macro))
                            continue
                        
                        # Check description match
                        if query_lower in macro.description.lower():
                            results.append((lib_name, macro_name, macro))
                            continue
                        
                        # Check tags match
                        if hasattr(macro, 'tags'):
                            for tag in macro.tags:
                                if query_lower in tag.lower():
                                    results.append((lib_name, macro_name, macro))
                                    break
                
                # Update statistics
                self.stats.search_queries += 1
                
                return results
                
        except Exception as e:
            logging.error(f"Error searching macros: {e}")
            return []
    
    def create_profile(self, name: str, description: str = "", 
                      category: MacroCategory = MacroCategory.CUSTOM) -> bool:
        """
        Create a new macro profile.
        
        Args:
            name: Profile name
            description: Profile description
            category: Profile category
            
        Returns:
            True if created successfully
        """
        try:
            with self.lock:
                profile = MacroProfile(
                    name=name,
                    description=description,
                    category=category
                )
                
                # Save profile
                self._save_profile(profile)
                
                self.stats.total_profiles += 1
                
                return True
                
        except Exception as e:
            logging.error(f"Error creating profile: {e}")
            return False
    
    def set_current_profile(self, profile_name: str) -> bool:
        """
        Set the current active profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if set successfully
        """
        try:
            with self.lock:
                profile_path = os.path.join(self.config.storage_path, 'profiles', f"{profile_name}.json")
                if not os.path.exists(profile_path):
                    return False
                
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_profile = MacroProfile(**data)
                
                return True
                
        except Exception as e:
            logging.error(f"Error setting current profile: {e}")
            return False
    
    def start_recording(self, macro_name: str, description: str = "", 
                       library_name: Optional[str] = None) -> bool:
        """
        Start recording a new macro.
        
        Args:
            macro_name: Macro name
            description: Macro description
            library_name: Target library name
            
        Returns:
            True if recording started successfully
        """
        try:
            with self.lock:
                if macro_name in self.active_recordings:
                    return False
                
                # Create recorder
                recorder_config = MacroRecorderConfig()
                recorder = MacroRecorder(recorder_config)
                
                # Start recording
                if recorder.start_recording(macro_name, description):
                    self.active_recordings[macro_name] = recorder
                    self.stats.active_recordings += 1
                    
                    # Trigger status callback
                    self._trigger_status_callbacks(macro_name, MacroStatus.RECORDING)
                    
                    return True
                
                return False
                
        except Exception as e:
            logging.error(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self, macro_name: str, library_name: Optional[str] = None) -> Optional[MacroRecording]:
        """
        Stop recording and save macro.
        
        Args:
            macro_name: Macro name
            library_name: Target library name
            
        Returns:
            Completed macro or None if error
        """
        try:
            with self.lock:
                if macro_name not in self.active_recordings:
                    return None
                
                recorder = self.active_recordings[macro_name]
                macro = recorder.stop_recording()
                
                if macro:
                    # Add to library
                    target_library = library_name or (self.current_profile.name if self.current_profile else "default")
                    if target_library not in self.libraries:
                        self.create_library(target_library)
                    
                    self.add_macro_to_library(target_library, macro)
                    
                    # Remove from active recordings
                    del self.active_recordings[macro_name]
                    self.stats.active_recordings -= 1
                    
                    # Trigger status callback
                    self._trigger_status_callbacks(macro_name, MacroStatus.ACTIVE)
                
                return macro
                
        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
            return None
    
    def start_playback(self, library_name: str, macro_name: str) -> bool:
        """
        Start playing a macro.
        
        Args:
            library_name: Library name
            macro_name: Macro name
            
        Returns:
            True if playback started successfully
        """
        try:
            with self.lock:
                macro = self.get_macro(library_name, macro_name)
                if not macro:
                    return False
                
                # Create player
                player_config = PlaybackConfig()
                player = MacroPlayer(player_config)
                
                # Load and start playback
                if player.load_recording(macro) and player.start_playback():
                    self.active_playbacks[macro_name] = player
                    self.stats.active_playbacks += 1
                    
                    # Trigger status callback
                    self._trigger_status_callbacks(macro_name, MacroStatus.PLAYING)
                    
                    return True
                
                return False
                
        except Exception as e:
            logging.error(f"Error starting playback: {e}")
            return False
    
    def stop_playback(self, macro_name: str) -> bool:
        """
        Stop playing a macro.
        
        Args:
            macro_name: Macro name
            
        Returns:
            True if stopped successfully
        """
        try:
            with self.lock:
                if macro_name not in self.active_playbacks:
                    return False
                
                player = self.active_playbacks[macro_name]
                player.stop_playback()
                
                # Remove from active playbacks
                del self.active_playbacks[macro_name]
                self.stats.active_playbacks -= 1
                
                # Trigger status callback
                self._trigger_status_callbacks(macro_name, MacroStatus.ACTIVE)
                
                return True
                
        except Exception as e:
            logging.error(f"Error stopping playback: {e}")
            return False
    
    def start_editing(self, library_name: str, macro_name: str) -> bool:
        """
        Start editing a macro.
        
        Args:
            library_name: Library name
            macro_name: Macro name
            
        Returns:
            True if editing started successfully
        """
        try:
            with self.lock:
                macro = self.get_macro(library_name, macro_name)
                if not macro:
                    return False
                
                # Create editor
                editor_config = EditorConfig()
                editor = MacroEditor(editor_config)
                
                # Load macro for editing
                if editor.load_recording(macro):
                    self.active_editors[macro_name] = editor
                    self.stats.active_editors += 1
                    
                    # Trigger status callback
                    self._trigger_status_callbacks(macro_name, MacroStatus.EDITING)
                    
                    return True
                
                return False
                
        except Exception as e:
            logging.error(f"Error starting editing: {e}")
            return False
    
    def stop_editing(self, macro_name: str, save: bool = True) -> bool:
        """
        Stop editing a macro.
        
        Args:
            macro_name: Macro name
            save: Whether to save changes
            
        Returns:
            True if stopped successfully
        """
        try:
            with self.lock:
                if macro_name not in self.active_editors:
                    return False
                
                editor = self.active_editors[macro_name]
                
                if save:
                    # Save changes
                    updated_macro = editor.save_recording()
                    if updated_macro:
                        # Update in library
                        for library in self.libraries.values():
                            if macro_name in library.macros:
                                library.macros[macro_name] = updated_macro
                                library.modified_at = time.time()
                                self._save_library(library)
                                break
                
                # Remove from active editors
                del self.active_editors[macro_name]
                self.stats.active_editors -= 1
                
                # Trigger status callback
                self._trigger_status_callbacks(macro_name, MacroStatus.ACTIVE)
                
                return True
                
        except Exception as e:
            logging.error(f"Error stopping editing: {e}")
            return False
    
    def export_library(self, library_name: str, filepath: str) -> bool:
        """
        Export a library to file.
        
        Args:
            library_name: Library name
            filepath: Export file path
            
        Returns:
            True if exported successfully
        """
        try:
            with self.lock:
                if library_name not in self.libraries:
                    return False
                
                library = self.libraries[library_name]
                
                # Create export data
                export_data = {
                    'library': library.to_dict(),
                    'exported_at': time.time(),
                    'version': '1.0'
                }
                
                # Save to file
                if filepath.endswith('.zip'):
                    # Export as ZIP
                    with zipfile.ZipFile(filepath, 'w') as zipf:
                        zipf.writestr('library.json', json.dumps(export_data, indent=2))
                else:
                    # Export as JSON
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.stats.export_operations += 1
                return True
                
        except Exception as e:
            logging.error(f"Error exporting library: {e}")
            return False
    
    def import_library(self, filepath: str) -> bool:
        """
        Import a library from file.
        
        Args:
            filepath: Import file path
            
        Returns:
            True if imported successfully
        """
        try:
            with self.lock:
                # Load data
                if filepath.endswith('.zip'):
                    # Import from ZIP
                    with zipfile.ZipFile(filepath, 'r') as zipf:
                        data = json.loads(zipf.read('library.json'))
                else:
                    # Import from JSON
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                # Create library
                library_data = data['library']
                library = MacroLibrary(**library_data)
                
                # Add to libraries
                self.libraries[library.name] = library
                self.stats.total_libraries += 1
                
                # Save library
                self._save_library(library)
                
                self.stats.import_operations += 1
                return True
                
        except Exception as e:
            logging.error(f"Error importing library: {e}")
            return False
    
    def _save_library(self, library: MacroLibrary):
        """Save a library to disk."""
        try:
            library_path = os.path.join(self.config.storage_path, 'libraries', f"{library.name}.json")
            with open(library_path, 'w', encoding='utf-8') as f:
                json.dump(library.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"Error saving library: {e}")
    
    def _save_profile(self, profile: MacroProfile):
        """Save a profile to disk."""
        try:
            profile_path = os.path.join(self.config.storage_path, 'profiles', f"{profile.name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"Error saving profile: {e}")
    
    def _create_backup(self):
        """Create a backup of all data."""
        try:
            backup_time = int(time.time())
            backup_dir = os.path.join(self.config.storage_path, 'backups', f"backup_{backup_time}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all data
            for subdir in ['macros', 'profiles', 'libraries']:
                src = os.path.join(self.config.storage_path, subdir)
                dst = os.path.join(backup_dir, subdir)
                if os.path.exists(src):
                    shutil.copytree(src, dst)
            
            # Update statistics
            self.stats.last_backup_time = time.time()
            
            # Clean old backups
            self._clean_old_backups()
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
    
    def _clean_old_backups(self):
        """Clean old backup files."""
        try:
            backup_dir = os.path.join(self.config.storage_path, 'backups')
            if not os.path.exists(backup_dir):
                return
            
            backups = []
            for item in os.listdir(backup_dir):
                if item.startswith('backup_'):
                    backup_path = os.path.join(backup_dir, item)
                    if os.path.isdir(backup_path):
                        backups.append((backup_path, os.path.getmtime(backup_path)))
            
            # Sort by modification time (oldest first)
            backups.sort(key=lambda x: x[1])
            
            # Remove old backups
            while len(backups) > self.config.max_backups:
                old_backup = backups.pop(0)
                shutil.rmtree(old_backup[0])
                
        except Exception as e:
            logging.error(f"Error cleaning old backups: {e}")
    
    def _auto_save_all(self):
        """Auto-save all active recordings and editors."""
        try:
            with self.lock:
                # Auto-save active recordings
                for recorder in self.active_recordings.values():
                    if hasattr(recorder, '_auto_save'):
                        recorder._auto_save()
                
                # Auto-save active editors
                for editor in self.active_editors.values():
                    if hasattr(editor, '_auto_save'):
                        editor._auto_save()
                
        except Exception as e:
            logging.error(f"Error in auto-save: {e}")
    
    def _trigger_change_callbacks(self, operation: str, macro_name: str):
        """Trigger change callbacks."""
        for callback in self.change_callbacks:
            try:
                callback(operation, macro_name)
            except Exception as e:
                logging.error(f"Error in change callback: {e}")
    
    def _trigger_status_callbacks(self, macro_name: str, status: MacroStatus):
        """Trigger status callbacks."""
        for callback in self.status_callbacks:
            try:
                callback(macro_name, status)
            except Exception as e:
                logging.error(f"Error in status callback: {e}")
    
    def add_change_callback(self, callback: Callable[[str, str], None]):
        """Add callback for changes."""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, str], None]):
        """Remove change callback."""
        try:
            self.change_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_status_callback(self, callback: Callable[[str, MacroStatus], None]):
        """Add callback for status changes."""
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[str, MacroStatus], None]):
        """Remove status callback."""
        try:
            self.status_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_stats(self) -> MacroManagerStats:
        """Get manager statistics."""
        with self.lock:
            return MacroManagerStats(
                total_macros=self.stats.total_macros,
                total_profiles=self.stats.total_profiles,
                total_libraries=self.stats.total_libraries,
                active_recordings=self.stats.active_recordings,
                active_playbacks=self.stats.active_playbacks,
                active_editors=self.stats.active_editors,
                storage_usage_mb=self.stats.storage_usage_mb,
                last_backup_time=self.stats.last_backup_time,
                last_index_time=self.stats.last_index_time,
                search_queries=self.stats.search_queries,
                import_operations=self.stats.import_operations,
                export_operations=self.stats.export_operations
            )
    
    def get_libraries(self) -> Dict[str, MacroLibrary]:
        """Get all libraries."""
        with self.lock:
            return self.libraries.copy()
    
    def get_current_profile(self) -> Optional[MacroProfile]:
        """Get current profile."""
        return self.current_profile
    
    def get_active_recordings(self) -> List[str]:
        """Get active recording names."""
        with self.lock:
            return list(self.active_recordings.keys())
    
    def get_active_playbacks(self) -> List[str]:
        """Get active playback names."""
        with self.lock:
            return list(self.active_playbacks.keys())
    
    def get_active_editors(self) -> List[str]:
        """Get active editor names."""
        with self.lock:
            return list(self.active_editors.keys())


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create macro manager
    config = MacroManagerConfig(
        enabled=True,
        storage_path="test_macros",
        backup_enabled=True,
        backup_interval=60.0,
        max_backups=5,
        auto_save=True,
        auto_save_interval=10.0,
        compression_enabled=True,
        version_control=True,
        max_versions=3,
        search_enabled=True,
        indexing_enabled=True
    )
    
    manager = MacroManager(config)
    
    # Add callbacks for testing
    def change_callback(operation: str, macro_name: str):
        print(f"Change: {operation} -> {macro_name}")
    
    def status_callback(macro_name: str, status: MacroStatus):
        print(f"Status: {macro_name} -> {status.value}")
    
    manager.add_change_callback(change_callback)
    manager.add_status_callback(status_callback)
    
    print("Testing Macro Manager...")
    
    # Test library creation
    if manager.create_library("Test Library", "A test library", "Test Author"):
        print("✓ Library created")
    
    # Test profile creation
    if manager.create_profile("Test Profile", "A test profile", MacroCategory.GAMING):
        print("✓ Profile created")
    
    # Test setting current profile
    if manager.set_current_profile("Test Profile"):
        print("✓ Current profile set")
    
    # Test macro recording
    if manager.start_recording("Test Macro", "A test macro", "Test Library"):
        print("✓ Recording started")
        
        # Simulate some recording time
        time.sleep(1.0)
        
        # Stop recording
        macro = manager.stop_recording("Test Macro", "Test Library")
        if macro:
            print(f"✓ Recording stopped: {macro.name} ({macro.event_count} events)")
    
    # Test macro playback
    if manager.start_playback("Test Library", "Test Macro"):
        print("✓ Playback started")
        
        # Simulate some playback time
        time.sleep(1.0)
        
        # Stop playback
        if manager.stop_playback("Test Macro"):
            print("✓ Playback stopped")
    
    # Test macro editing
    if manager.start_editing("Test Library", "Test Macro"):
        print("✓ Editing started")
        
        # Simulate some editing time
        time.sleep(1.0)
        
        # Stop editing
        if manager.stop_editing("Test Macro", save=True):
            print("✓ Editing stopped")
    
    # Test search
    results = manager.search_macros("test")
    print(f"✓ Search results: {len(results)} macros found")
    
    # Test export/import
    if manager.export_library("Test Library", "test_library.json"):
        print("✓ Library exported")
    
    # Test statistics
    stats = manager.get_stats()
    print(f"\nManager Statistics:")
    print(f"  - Total macros: {stats.total_macros}")
    print(f"  - Total profiles: {stats.total_profiles}")
    print(f"  - Total libraries: {stats.total_libraries}")
    print(f"  - Active recordings: {stats.active_recordings}")
    print(f"  - Active playbacks: {stats.active_playbacks}")
    print(f"  - Active editors: {stats.active_editors}")
    print(f"  - Search queries: {stats.search_queries}")
    print(f"  - Import operations: {stats.import_operations}")
    print(f"  - Export operations: {stats.export_operations}")
    
    print("\nMacro manager testing completed!")
