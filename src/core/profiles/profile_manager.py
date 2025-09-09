"""
Profile Manager for ZeroLag

This module implements comprehensive profile management functionality including:
- Profile creation, deletion, and switching
- Save/load profile data to/from JSON files
- Profile validation and error handling
- Profile metadata management
- Profile backup and restore functionality
- Integration with ZeroLag system components

Features:
- Centralized profile management
- Real-time profile switching
- Profile validation and compatibility checking
- Backup and restore functionality
- Performance monitoring
- Integration with all ZeroLag components
"""

import os
import json
import shutil
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .profile import Profile, ProfileMetadata, GamingMode


@dataclass
class ProfileManagerConfig:
    """Configuration for profile manager."""
    profiles_directory: str = "profiles"
    backup_directory: str = "profiles/backups"
    auto_save: bool = True
    auto_save_interval: float = 30.0  # seconds
    max_backups: int = 10
    backup_retention_days: int = 30
    validate_on_load: bool = True
    create_backup_on_switch: bool = True
    compression_enabled: bool = True


@dataclass
class ProfileManagerStats:
    """Statistics for profile manager."""
    total_profiles: int = 0
    active_profile: Optional[str] = None
    profiles_loaded: int = 0
    profiles_saved: int = 0
    profiles_switched: int = 0
    profiles_created: int = 0
    profiles_deleted: int = 0
    backup_operations: int = 0
    restore_operations: int = 0
    validation_errors: int = 0
    last_operation_time: float = 0.0
    storage_usage_mb: float = 0.0


class ProfileManager:
    """
    Comprehensive profile management system for ZeroLag.
    
    Handles all profile operations including creation, deletion, switching,
    validation, backup, and restore functionality.
    """
    
    def __init__(self, config: Optional[ProfileManagerConfig] = None):
        """
        Initialize profile manager.
        
        Args:
            config: Manager configuration
        """
        self.config = config or ProfileManagerConfig()
        self.profiles: Dict[str, Profile] = {}
        self.active_profile: Optional[str] = None
        self.stats = ProfileManagerStats()
        
        # Threading
        self.lock = threading.RLock()
        
        # Callbacks
        self.profile_switch_callbacks: List[Callable[[str, str], None]] = []  # (old_profile, new_profile)
        self.profile_save_callbacks: List[Callable[[str], None]] = []  # (profile_name)
        self.profile_load_callbacks: List[Callable[[str], None]] = []  # (profile_name)
        
        # Auto-save
        self.auto_save_timer: Optional[threading.Timer] = None
        self.auto_save_enabled = self.config.auto_save
        
        # Initialize directories
        self._initialize_directories()
        
        # Load existing profiles
        self._load_all_profiles()
    
    def _initialize_directories(self):
        """Initialize profile and backup directories."""
        try:
            Path(self.config.profiles_directory).mkdir(parents=True, exist_ok=True)
            Path(self.config.backup_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating profile directories: {e}")
    
    def _load_all_profiles(self):
        """Load all profiles from the profiles directory."""
        try:
            profiles_dir = Path(self.config.profiles_directory)
            if not profiles_dir.exists():
                return
            
            for profile_file in profiles_dir.glob("*.json"):
                if profile_file.is_file():
                    profile = Profile.load_from_file(profile_file)
                    if profile:
                        self.profiles[profile.metadata.name] = profile
                        self.stats.profiles_loaded += 1
            
            self.stats.total_profiles = len(self.profiles)
            logging.info(f"Loaded {self.stats.total_profiles} profiles")
            
        except Exception as e:
            logging.error(f"Error loading profiles: {e}")
    
    def create_profile(self, name: str, description: str = "", 
                      gaming_mode: GamingMode = GamingMode.GENERAL,
                      based_on: Optional[str] = None) -> bool:
        """
        Create a new profile.
        
        Args:
            name: Profile name
            description: Profile description
            gaming_mode: Gaming mode category
            based_on: Name of profile to base this on (optional)
            
        Returns:
            True if profile created successfully
        """
        try:
            with self.lock:
                if name in self.profiles:
                    logging.warning(f"Profile '{name}' already exists")
                    return False
                
                # Create new profile
                if based_on and based_on in self.profiles:
                    # Clone existing profile
                    profile = self.profiles[based_on].clone(name)
                    profile.metadata.description = description
                    profile.metadata.gaming_mode = gaming_mode
                else:
                    # Create from scratch
                    profile = Profile()
                    profile.metadata.name = name
                    profile.metadata.description = description
                    profile.metadata.gaming_mode = gaming_mode
                
                # Save profile
                if self._save_profile(profile):
                    self.profiles[name] = profile
                    self.stats.total_profiles += 1
                    self.stats.profiles_created += 1
                    self.stats.last_operation_time = time.time()
                    
                    # Trigger callbacks
                    self._trigger_profile_load_callbacks(name)
                    
                    logging.info(f"Created profile: {name}")
                    return True
                
        except Exception as e:
            logging.error(f"Error creating profile '{name}': {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def delete_profile(self, name: str, create_backup: bool = True) -> bool:
        """
        Delete a profile.
        
        Args:
            name: Profile name
            create_backup: Whether to create backup before deletion
            
        Returns:
            True if profile deleted successfully
        """
        try:
            with self.lock:
                if name not in self.profiles:
                    logging.warning(f"Profile '{name}' not found")
                    return False
                
                # Create backup if requested
                if create_backup:
                    self._create_backup(name)
                
                # Remove from active if it's the current profile
                if self.active_profile == name:
                    self.active_profile = None
                    self.stats.active_profile = None
                
                # Delete file
                profile_file = Path(self.config.profiles_directory) / f"{name}.json"
                if profile_file.exists():
                    profile_file.unlink()
                
                # Remove from memory
                del self.profiles[name]
                self.stats.total_profiles -= 1
                self.stats.profiles_deleted += 1
                self.stats.last_operation_time = time.time()
                
                logging.info(f"Deleted profile: {name}")
                return True
                
        except Exception as e:
            logging.error(f"Error deleting profile '{name}': {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def switch_profile(self, name: str, apply_settings: bool = True) -> bool:
        """
        Switch to a different profile.
        
        Args:
            name: Profile name to switch to
            apply_settings: Whether to apply settings to system
            
        Returns:
            True if profile switched successfully
        """
        try:
            with self.lock:
                if name not in self.profiles:
                    logging.warning(f"Profile '{name}' not found")
                    return False
                
                old_profile = self.active_profile
                self.active_profile = name
                self.stats.active_profile = name
                self.stats.profiles_switched += 1
                self.stats.last_operation_time = time.time()
                
                # Create backup of old profile if enabled
                if (self.config.create_backup_on_switch and 
                    old_profile and old_profile in self.profiles):
                    self._create_backup(old_profile)
                
                # Trigger callbacks
                self._trigger_profile_switch_callbacks(old_profile, name)
                
                logging.info(f"Switched to profile: {name}")
                return True
                
        except Exception as e:
            logging.error(f"Error switching to profile '{name}': {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name."""
        with self.lock:
            return self.profiles.get(name)
    
    def get_active_profile(self) -> Optional[Profile]:
        """Get the currently active profile."""
        with self.lock:
            if self.active_profile:
                return self.profiles.get(self.active_profile)
        return None
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names."""
        with self.lock:
            return list(self.profiles.keys())
    
    def get_profiles_by_mode(self, gaming_mode: GamingMode) -> List[str]:
        """Get profiles filtered by gaming mode."""
        with self.lock:
            return [
                name for name, profile in self.profiles.items()
                if profile.metadata.gaming_mode == gaming_mode
            ]
    
    def save_profile(self, name: str) -> bool:
        """Save a profile to file."""
        try:
            with self.lock:
                if name not in self.profiles:
                    return False
                
                profile = self.profiles[name]
                if self._save_profile(profile):
                    self.stats.profiles_saved += 1
                    self.stats.last_operation_time = time.time()
                    
                    # Trigger callbacks
                    self._trigger_profile_save_callbacks(name)
                    
                    return True
                
        except Exception as e:
            logging.error(f"Error saving profile '{name}': {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def save_all_profiles(self) -> int:
        """Save all profiles to files."""
        saved_count = 0
        with self.lock:
            for name in self.profiles:
                if self.save_profile(name):
                    saved_count += 1
        return saved_count
    
    def _save_profile(self, profile: Profile) -> bool:
        """Internal method to save profile to file."""
        try:
            profile_file = Path(self.config.profiles_directory) / f"{profile.metadata.name}.json"
            return profile.save_to_file(profile_file)
        except Exception as e:
            logging.error(f"Error saving profile to file: {e}")
            return False
    
    def load_profile(self, file_path: Union[str, Path]) -> bool:
        """Load a profile from file."""
        try:
            profile = Profile.load_from_file(file_path)
            if profile:
                with self.lock:
                    self.profiles[profile.metadata.name] = profile
                    self.stats.total_profiles += 1
                    self.stats.profiles_loaded += 1
                    self.stats.last_operation_time = time.time()
                    
                    # Trigger callbacks
                    self._trigger_profile_load_callbacks(profile.metadata.name)
                
                logging.info(f"Loaded profile: {profile.metadata.name}")
                return True
                
        except Exception as e:
            logging.error(f"Error loading profile from {file_path}: {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def export_profile(self, name: str, file_path: Union[str, Path]) -> bool:
        """Export a profile to a specific file."""
        try:
            with self.lock:
                if name not in self.profiles:
                    return False
                
                profile = self.profiles[name]
                return profile.save_to_file(file_path)
                
        except Exception as e:
            logging.error(f"Error exporting profile '{name}': {e}")
            return False
    
    def import_profile(self, file_path: Union[str, Path], 
                      new_name: Optional[str] = None) -> bool:
        """Import a profile from file."""
        try:
            profile = Profile.load_from_file(file_path)
            if profile:
                # Rename if requested
                if new_name:
                    profile.metadata.name = new_name
                
                # Check for name conflicts
                original_name = profile.metadata.name
                counter = 1
                while profile.metadata.name in self.profiles:
                    profile.metadata.name = f"{original_name} ({counter})"
                    counter += 1
                
                with self.lock:
                    self.profiles[profile.metadata.name] = profile
                    self.stats.total_profiles += 1
                    self.stats.profiles_loaded += 1
                    self.stats.last_operation_time = time.time()
                    
                    # Save to profiles directory
                    self._save_profile(profile)
                    
                    # Trigger callbacks
                    self._trigger_profile_load_callbacks(profile.metadata.name)
                
                logging.info(f"Imported profile: {profile.metadata.name}")
                return True
                
        except Exception as e:
            logging.error(f"Error importing profile from {file_path}: {e}")
            self.stats.validation_errors += 1
        
        return False
    
    def _create_backup(self, profile_name: str) -> bool:
        """Create a backup of a profile."""
        try:
            if profile_name not in self.profiles:
                return False
            
            profile = self.profiles[profile_name]
            timestamp = int(time.time())
            backup_file = Path(self.config.backup_directory) / f"{profile_name}_{timestamp}.json"
            
            if profile.save_to_file(backup_file):
                self.stats.backup_operations += 1
                logging.info(f"Created backup: {backup_file}")
                return True
                
        except Exception as e:
            logging.error(f"Error creating backup for '{profile_name}': {e}")
        
        return False
    
    def restore_profile(self, profile_name: str, backup_file: Union[str, Path]) -> bool:
        """Restore a profile from backup."""
        try:
            profile = Profile.load_from_file(backup_file)
            if profile:
                with self.lock:
                    self.profiles[profile_name] = profile
                    self._save_profile(profile)
                    self.stats.restore_operations += 1
                    self.stats.last_operation_time = time.time()
                
                logging.info(f"Restored profile from backup: {profile_name}")
                return True
                
        except Exception as e:
            logging.error(f"Error restoring profile '{profile_name}': {e}")
        
        return False
    
    def get_backups(self, profile_name: str) -> List[Path]:
        """Get list of backup files for a profile."""
        try:
            backup_dir = Path(self.config.backup_directory)
            pattern = f"{profile_name}_*.json"
            return list(backup_dir.glob(pattern))
        except Exception as e:
            logging.error(f"Error getting backups for '{profile_name}': {e}")
            return []
    
    def cleanup_old_backups(self) -> int:
        """Clean up old backup files."""
        cleaned_count = 0
        try:
            backup_dir = Path(self.config.backup_directory)
            cutoff_time = time.time() - (self.config.backup_retention_days * 24 * 3600)
            
            for backup_file in backup_dir.glob("*.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    cleaned_count += 1
            
            logging.info(f"Cleaned up {cleaned_count} old backup files")
            
        except Exception as e:
            logging.error(f"Error cleaning up backups: {e}")
        
        return cleaned_count
    
    def get_stats(self) -> ProfileManagerStats:
        """Get profile manager statistics."""
        with self.lock:
            # Calculate storage usage
            total_size = 0
            profiles_dir = Path(self.config.profiles_directory)
            if profiles_dir.exists():
                for file_path in profiles_dir.glob("*.json"):
                    total_size += file_path.stat().st_size
            
            self.stats.storage_usage_mb = total_size / (1024 * 1024)
            return self.stats
    
    def add_profile_switch_callback(self, callback: Callable[[str, str], None]):
        """Add callback for profile switching."""
        self.profile_switch_callbacks.append(callback)
    
    def add_profile_save_callback(self, callback: Callable[[str], None]):
        """Add callback for profile saving."""
        self.profile_save_callbacks.append(callback)
    
    def add_profile_load_callback(self, callback: Callable[[str], None]):
        """Add callback for profile loading."""
        self.profile_load_callbacks.append(callback)
    
    def _trigger_profile_switch_callbacks(self, old_profile: Optional[str], new_profile: str):
        """Trigger profile switch callbacks."""
        for callback in self.profile_switch_callbacks:
            try:
                callback(old_profile, new_profile)
            except Exception as e:
                logging.error(f"Error in profile switch callback: {e}")
    
    def _trigger_profile_save_callbacks(self, profile_name: str):
        """Trigger profile save callbacks."""
        for callback in self.profile_save_callbacks:
            try:
                callback(profile_name)
            except Exception as e:
                logging.error(f"Error in profile save callback: {e}")
    
    def _trigger_profile_load_callbacks(self, profile_name: str):
        """Trigger profile load callbacks."""
        for callback in self.profile_load_callbacks:
            try:
                callback(profile_name)
            except Exception as e:
                logging.error(f"Error in profile load callback: {e}")
    
    def start_auto_save(self):
        """Start auto-save functionality."""
        if self.auto_save_enabled:
            self._schedule_auto_save()
    
    def stop_auto_save(self):
        """Stop auto-save functionality."""
        self.auto_save_enabled = False
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
            self.auto_save_timer = None
    
    def _schedule_auto_save(self):
        """Schedule the next auto-save."""
        if self.auto_save_enabled:
            self.auto_save_timer = threading.Timer(
                self.config.auto_save_interval,
                self._auto_save_callback
            )
            self.auto_save_timer.start()
    
    def _auto_save_callback(self):
        """Auto-save callback."""
        try:
            self.save_all_profiles()
            self._schedule_auto_save()
        except Exception as e:
            logging.error(f"Error in auto-save: {e}")
    
    def cleanup(self):
        """Clean up profile manager resources."""
        self.stop_auto_save()
        self.save_all_profiles()
        self.cleanup_old_backups()


# Example usage and testing
if __name__ == "__main__":
    # Create profile manager
    config = ProfileManagerConfig(
        profiles_directory="test_profiles",
        auto_save=True,
        auto_save_interval=10.0
    )
    manager = ProfileManager(config)
    
    # Create some test profiles
    manager.create_profile("FPS Profile", "Optimized for FPS games", GamingMode.FPS)
    manager.create_profile("MOBA Profile", "Optimized for MOBA games", GamingMode.MOBA)
    
    # Switch between profiles
    manager.switch_profile("FPS Profile")
    print(f"Active profile: {manager.get_active_profile().metadata.name}")
    
    # List all profiles
    print(f"All profiles: {manager.list_profiles()}")
    
    # Get statistics
    stats = manager.get_stats()
    print(f"Total profiles: {stats.total_profiles}")
    print(f"Storage usage: {stats.storage_usage_mb:.2f} MB")
    
    # Cleanup
    manager.cleanup()
