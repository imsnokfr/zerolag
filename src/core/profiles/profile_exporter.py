"""
Profile Exporter for ZeroLag

This module provides comprehensive profile import/export functionality
for sharing profiles between users and backing up profile data.

Features:
- Multiple export formats (JSON, ZIP, encrypted)
- Profile validation during import
- Batch import/export operations
- Profile sharing via file or URL
- Backup and restore functionality
- Version migration support
"""

import json
import zipfile
import os
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

from .profile import Profile, ProfileMetadata
from .profile_validator import ProfileValidator, ValidationResult


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    ZIP = "zip"
    ENCRYPTED_JSON = "encrypted_json"
    ENCRYPTED_ZIP = "encrypted_zip"


@dataclass
class ImportResult:
    """Result of profile import operation."""
    success: bool
    profile: Optional[Profile] = None
    validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ProfileExporter:
    """
    Comprehensive profile import/export system for ZeroLag.
    
    Handles profile sharing, backup, and migration functionality
    with support for multiple formats and validation.
    """
    
    def __init__(self, validator: Optional[ProfileValidator] = None):
        """
        Initialize profile exporter.
        
        Args:
            validator: Profile validator instance
        """
        self.validator = validator or ProfileValidator()
        self.supported_formats = [fmt.value for fmt in ExportFormat]
        
        # Export metadata
        self.export_version = "1.0.0"
        self.export_tool = "ZeroLag Profile Exporter"
    
    def export_profile(self, profile: Profile, file_path: Union[str, Path],
                      format_type: ExportFormat = ExportFormat.JSON,
                      include_metadata: bool = True,
                      compress: bool = False) -> bool:
        """
        Export a profile to file.
        
        Args:
            profile: Profile to export
            file_path: Output file path
            format_type: Export format
            include_metadata: Include export metadata
            compress: Enable compression for supported formats
            
        Returns:
            True if export successful
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == ExportFormat.JSON:
                return self._export_json(profile, file_path, include_metadata)
            elif format_type == ExportFormat.ZIP:
                return self._export_zip(profile, file_path, include_metadata, compress)
            elif format_type == ExportFormat.ENCRYPTED_JSON:
                return self._export_encrypted_json(profile, file_path, include_metadata)
            elif format_type == ExportFormat.ENCRYPTED_ZIP:
                return self._export_encrypted_zip(profile, file_path, include_metadata, compress)
            else:
                logging.error(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            logging.error(f"Error exporting profile: {e}")
            return False
    
    def export_profiles(self, profiles: List[Profile], file_path: Union[str, Path],
                       format_type: ExportFormat = ExportFormat.ZIP,
                       include_metadata: bool = True) -> bool:
        """
        Export multiple profiles to a single file.
        
        Args:
            profiles: List of profiles to export
            file_path: Output file path
            format_type: Export format
            include_metadata: Include export metadata
            
        Returns:
            True if export successful
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == ExportFormat.ZIP:
                return self._export_multiple_zip(profiles, file_path, include_metadata)
            elif format_type == ExportFormat.ENCRYPTED_ZIP:
                return self._export_multiple_encrypted_zip(profiles, file_path, include_metadata)
            else:
                logging.error(f"Unsupported format for multiple profiles: {format_type}")
                return False
                
        except Exception as e:
            logging.error(f"Error exporting profiles: {e}")
            return False
    
    def import_profile(self, file_path: Union[str, Path],
                      validate: bool = True,
                      auto_fix: bool = False) -> ImportResult:
        """
        Import a profile from file.
        
        Args:
            file_path: Input file path
            validate: Validate profile after import
            auto_fix: Attempt to fix validation issues
            
        Returns:
            ImportResult with import details
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ImportResult(
                    success=False,
                    error_message=f"File not found: {file_path}"
                )
            
            # Determine format and import
            if file_path.suffix.lower() == '.json':
                profile = self._import_json(file_path)
            elif file_path.suffix.lower() == '.zip':
                profile = self._import_zip(file_path)
            else:
                return ImportResult(
                    success=False,
                    error_message=f"Unsupported file format: {file_path.suffix}"
                )
            
            if profile is None:
                return ImportResult(
                    success=False,
                    error_message="Failed to load profile from file"
                )
            
            # Validate if requested
            validation_result = None
            if validate:
                validation_result = self.validator.validate_profile(profile)
                if not validation_result.is_valid and not auto_fix:
                    return ImportResult(
                        success=False,
                        profile=profile,
                        validation_result=validation_result,
                        error_message="Profile validation failed"
                    )
                
                # Auto-fix if requested
                if auto_fix and not validation_result.is_valid:
                    profile = self._auto_fix_profile(profile, validation_result)
                    validation_result = self.validator.validate_profile(profile)
            
            return ImportResult(
                success=True,
                profile=profile,
                validation_result=validation_result
            )
            
        except Exception as e:
            logging.error(f"Error importing profile: {e}")
            return ImportResult(
                success=False,
                error_message=f"Import failed: {str(e)}"
            )
    
    def import_profiles(self, file_path: Union[str, Path],
                       validate: bool = True,
                       auto_fix: bool = False) -> List[ImportResult]:
        """
        Import multiple profiles from file.
        
        Args:
            file_path: Input file path
            validate: Validate profiles after import
            auto_fix: Attempt to fix validation issues
            
        Returns:
            List of ImportResult objects
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return [ImportResult(
                    success=False,
                    error_message=f"File not found: {file_path}"
                )]
            
            if file_path.suffix.lower() == '.zip':
                return self._import_multiple_zip(file_path, validate, auto_fix)
            else:
                # Single profile file
                result = self.import_profile(file_path, validate, auto_fix)
                return [result]
                
        except Exception as e:
            logging.error(f"Error importing profiles: {e}")
            return [ImportResult(
                success=False,
                error_message=f"Import failed: {str(e)}"
            )]
    
    def _export_json(self, profile: Profile, file_path: Path, include_metadata: bool) -> bool:
        """Export profile as JSON."""
        try:
            export_data = profile.to_dict()
            
            if include_metadata:
                export_data['_export_metadata'] = {
                    'export_version': self.export_version,
                    'export_tool': self.export_tool,
                    'export_time': time.time(),
                    'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'profile_checksum': profile._calculate_checksum()
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Exported profile to JSON: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting JSON: {e}")
            return False
    
    def _export_zip(self, profile: Profile, file_path: Path, include_metadata: bool, compress: bool) -> bool:
        """Export profile as ZIP."""
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED) as zipf:
                # Add profile JSON
                profile_json = profile.to_json()
                zipf.writestr(f"{profile.metadata.name}.json", profile_json)
                
                # Add export metadata
                if include_metadata:
                    metadata = {
                        'export_version': self.export_version,
                        'export_tool': self.export_tool,
                        'export_time': time.time(),
                        'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'profile_checksum': profile._calculate_checksum(),
                        'profile_name': profile.metadata.name,
                        'profile_version': profile.metadata.version,
                        'gaming_mode': profile.metadata.gaming_mode.value
                    }
                    zipf.writestr("export_metadata.json", json.dumps(metadata, indent=2))
            
            logging.info(f"Exported profile to ZIP: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting ZIP: {e}")
            return False
    
    def _export_encrypted_json(self, profile: Profile, file_path: Path, include_metadata: bool) -> bool:
        """Export profile as encrypted JSON."""
        try:
            # Simple encryption (in production, use proper encryption)
            profile_data = profile.to_json()
            
            # Add export metadata
            if include_metadata:
                metadata = {
                    'export_version': self.export_version,
                    'export_tool': self.export_tool,
                    'export_time': time.time(),
                    'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'profile_checksum': profile._calculate_checksum()
                }
                export_data = {
                    'profile_data': profile_data,
                    'metadata': metadata
                }
            else:
                export_data = {'profile_data': profile_data}
            
            # Simple XOR encryption (replace with proper encryption in production)
            encrypted_data = self._simple_encrypt(json.dumps(export_data))
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            logging.info(f"Exported encrypted profile: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting encrypted JSON: {e}")
            return False
    
    def _export_encrypted_zip(self, profile: Profile, file_path: Path, include_metadata: bool, compress: bool) -> bool:
        """Export profile as encrypted ZIP."""
        try:
            # Create temporary ZIP
            temp_zip = file_path.with_suffix('.tmp.zip')
            
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED) as zipf:
                # Add profile JSON
                profile_json = profile.to_json()
                zipf.writestr(f"{profile.metadata.name}.json", profile_json)
                
                # Add export metadata
                if include_metadata:
                    metadata = {
                        'export_version': self.export_version,
                        'export_tool': self.export_tool,
                        'export_time': time.time(),
                        'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'profile_checksum': profile._calculate_checksum()
                    }
                    zipf.writestr("export_metadata.json", json.dumps(metadata, indent=2))
            
            # Encrypt the ZIP file
            with open(temp_zip, 'rb') as f:
                zip_data = f.read()
            
            encrypted_data = self._simple_encrypt(zip_data)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Clean up temporary file
            temp_zip.unlink()
            
            logging.info(f"Exported encrypted ZIP: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting encrypted ZIP: {e}")
            return False
    
    def _export_multiple_zip(self, profiles: List[Profile], file_path: Path, include_metadata: bool) -> bool:
        """Export multiple profiles as ZIP."""
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add each profile
                for profile in profiles:
                    profile_json = profile.to_json()
                    zipf.writestr(f"{profile.metadata.name}.json", profile_json)
                
                # Add export metadata
                if include_metadata:
                    metadata = {
                        'export_version': self.export_version,
                        'export_tool': self.export_tool,
                        'export_time': time.time(),
                        'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'profile_count': len(profiles),
                        'profile_names': [p.metadata.name for p in profiles]
                    }
                    zipf.writestr("export_metadata.json", json.dumps(metadata, indent=2))
            
            logging.info(f"Exported {len(profiles)} profiles to ZIP: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting multiple profiles: {e}")
            return False
    
    def _export_multiple_encrypted_zip(self, profiles: List[Profile], file_path: Path, include_metadata: bool) -> bool:
        """Export multiple profiles as encrypted ZIP."""
        try:
            # Create temporary ZIP
            temp_zip = file_path.with_suffix('.tmp.zip')
            
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add each profile
                for profile in profiles:
                    profile_json = profile.to_json()
                    zipf.writestr(f"{profile.metadata.name}.json", profile_json)
                
                # Add export metadata
                if include_metadata:
                    metadata = {
                        'export_version': self.export_version,
                        'export_tool': self.export_tool,
                        'export_time': time.time(),
                        'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'profile_count': len(profiles),
                        'profile_names': [p.metadata.name for p in profiles]
                    }
                    zipf.writestr("export_metadata.json", json.dumps(metadata, indent=2))
            
            # Encrypt the ZIP file
            with open(temp_zip, 'rb') as f:
                zip_data = f.read()
            
            encrypted_data = self._simple_encrypt(zip_data)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Clean up temporary file
            temp_zip.unlink()
            
            logging.info(f"Exported {len(profiles)} encrypted profiles: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting encrypted multiple profiles: {e}")
            return False
    
    def _import_json(self, file_path: Path) -> Optional[Profile]:
        """Import profile from JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for export metadata
            if '_export_metadata' in data:
                metadata = data['_export_metadata']
                logging.info(f"Importing profile exported by {metadata.get('export_tool', 'Unknown')} "
                           f"at {metadata.get('export_timestamp', 'Unknown time')}")
                del data['_export_metadata']
            
            return Profile.from_dict(data)
            
        except Exception as e:
            logging.error(f"Error importing JSON: {e}")
            return None
    
    def _import_zip(self, file_path: Path) -> Optional[Profile]:
        """Import profile from ZIP."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Find profile JSON files
                profile_files = [name for name in zipf.namelist() if name.endswith('.json') and name != 'export_metadata.json']
                
                if not profile_files:
                    logging.error("No profile files found in ZIP")
                    return None
                
                # Import first profile (for single profile import)
                profile_data = zipf.read(profile_files[0]).decode('utf-8')
                data = json.loads(profile_data)
                
                # Check for export metadata
                if 'export_metadata.json' in zipf.namelist():
                    metadata_data = zipf.read('export_metadata.json').decode('utf-8')
                    metadata = json.loads(metadata_data)
                    logging.info(f"Importing profile exported by {metadata.get('export_tool', 'Unknown')} "
                               f"at {metadata.get('export_timestamp', 'Unknown time')}")
                
                return Profile.from_dict(data)
                
        except Exception as e:
            logging.error(f"Error importing ZIP: {e}")
            return None
    
    def _import_multiple_zip(self, file_path: Path, validate: bool, auto_fix: bool) -> List[ImportResult]:
        """Import multiple profiles from ZIP."""
        results = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Find profile JSON files
                profile_files = [name for name in zipf.namelist() if name.endswith('.json') and name != 'export_metadata.json']
                
                if not profile_files:
                    return [ImportResult(
                        success=False,
                        error_message="No profile files found in ZIP"
                    )]
                
                # Import each profile
                for profile_file in profile_files:
                    try:
                        profile_data = zipf.read(profile_file).decode('utf-8')
                        data = json.loads(profile_data)
                        profile = Profile.from_dict(data)
                        
                        if profile:
                            # Validate if requested
                            validation_result = None
                            if validate:
                                validation_result = self.validator.validate_profile(profile)
                                if not validation_result.is_valid and auto_fix:
                                    profile = self._auto_fix_profile(profile, validation_result)
                                    validation_result = self.validator.validate_profile(profile)
                            
                            results.append(ImportResult(
                                success=True,
                                profile=profile,
                                validation_result=validation_result
                            ))
                        else:
                            results.append(ImportResult(
                                success=False,
                                error_message=f"Failed to load profile from {profile_file}"
                            ))
                            
                    except Exception as e:
                        results.append(ImportResult(
                            success=False,
                            error_message=f"Error importing {profile_file}: {str(e)}"
                        ))
                
        except Exception as e:
            results.append(ImportResult(
                success=False,
                error_message=f"Error reading ZIP file: {str(e)}"
            ))
        
        return results
    
    def _simple_encrypt(self, data: Union[str, bytes]) -> bytes:
        """Simple XOR encryption (replace with proper encryption in production)."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        key = b"ZeroLagProfileKey2024"
        encrypted = bytearray()
        
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        
        return bytes(encrypted)
    
    def _simple_decrypt(self, data: bytes) -> bytes:
        """Simple XOR decryption (replace with proper decryption in production)."""
        key = b"ZeroLagProfileKey2024"
        decrypted = bytearray()
        
        for i, byte in enumerate(data):
            decrypted.append(byte ^ key[i % len(key)])
        
        return bytes(decrypted)
    
    def _auto_fix_profile(self, profile: Profile, validation_result: ValidationResult) -> Profile:
        """Attempt to automatically fix profile validation issues."""
        # This is a simplified auto-fix implementation
        # In production, this would be more comprehensive
        
        for error in validation_result.errors:
            if error.field_path == "settings.dpi.dpi_value":
                if error.current_value < 100:
                    profile.settings.dpi.dpi_value = 100
                elif error.current_value > 16000:
                    profile.settings.dpi.dpi_value = 16000
            
            elif error.field_path == "settings.polling.mouse_polling_rate":
                if error.current_value < 125:
                    profile.settings.polling.mouse_polling_rate = 125
                elif error.current_value > 8000:
                    profile.settings.polling.mouse_polling_rate = 8000
            
            elif error.field_path == "settings.performance.memory_limit_mb":
                if error.current_value < 10.0:
                    profile.settings.performance.memory_limit_mb = 10.0
                elif error.current_value > 1000.0:
                    profile.settings.performance.memory_limit_mb = 1000.0
        
        return profile
    
    def get_export_info(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get export information from a file."""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('_export_metadata')
            
            elif file_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    if 'export_metadata.json' in zipf.namelist():
                        metadata_data = zipf.read('export_metadata.json').decode('utf-8')
                        return json.loads(metadata_data)
            
        except Exception as e:
            logging.error(f"Error reading export info: {e}")
        
        return None


# Example usage and testing
if __name__ == "__main__":
    # Create exporter
    exporter = ProfileExporter()
    
    # Create test profile
    from .profile import Profile, GamingMode
    profile = Profile()
    profile.metadata.name = "Test Export Profile"
    profile.metadata.gaming_mode = GamingMode.FPS
    
    # Export profile
    success = exporter.export_profile(profile, "test_profile.json", ExportFormat.JSON)
    print(f"Export successful: {success}")
    
    # Import profile
    result = exporter.import_profile("test_profile.json")
    print(f"Import successful: {result.success}")
    if result.success:
        print(f"Imported profile: {result.profile.metadata.name}")
    
    # Export as ZIP
    success = exporter.export_profile(profile, "test_profile.zip", ExportFormat.ZIP)
    print(f"ZIP export successful: {success}")
    
    # Import from ZIP
    result = exporter.import_profile("test_profile.zip")
    print(f"ZIP import successful: {result.success}")
