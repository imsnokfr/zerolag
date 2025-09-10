"""
Profile Library Management System

This module provides functionality for managing a local library of
community profiles with search, filtering, and categorization.

Features:
- Local profile library management
- Search and filtering capabilities
- Profile categorization
- Offline profile access
- Profile synchronization
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from .profile_sharing import CommunityProfile, ProfileCategory, ProfileDifficulty

logger = logging.getLogger(__name__)

class SortOrder(Enum):
    """Sort order options for profile searches."""
    NEWEST = "newest"
    OLDEST = "oldest"
    MOST_DOWNLOADED = "most_downloaded"
    LEAST_DOWNLOADED = "least_downloaded"
    HIGHEST_RATED = "highest_rated"
    LOWEST_RATED = "lowest_rated"
    ALPHABETICAL = "alphabetical"
    REVERSE_ALPHABETICAL = "reverse_alphabetical"

@dataclass
class ProfileSearchFilter:
    """Filter criteria for profile searches."""
    categories: Set[ProfileCategory] = field(default_factory=set)
    difficulties: Set[ProfileDifficulty] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    authors: Set[str] = field(default_factory=set)
    min_rating: float = 0.0
    max_rating: float = 5.0
    min_downloads: int = 0
    max_downloads: int = 0
    verified_only: bool = False
    featured_only: bool = False
    compatibility: Set[str] = field(default_factory=set)
    search_text: str = ""
    sort_order: SortOrder = SortOrder.NEWEST
    limit: Optional[int] = None

class ProfileLibrary:
    """Local profile library for managing community profiles."""
    
    def __init__(self, library_path: Path):
        self.library_path = Path(library_path)
        self.profiles: Dict[str, CommunityProfile] = {}
        self.metadata: Dict[str, Any] = {
            "last_sync": 0,
            "total_profiles": 0,
            "categories": {},
            "tags": {},
            "authors": {}
        }
        self.logger = logging.getLogger(__name__)
        
        # Ensure library directory exists
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing library
        self._load_library()
    
    def add_profile(self, profile: CommunityProfile) -> bool:
        """Add a profile to the library."""
        try:
            self.profiles[profile.profile_id] = profile
            self._update_metadata(profile)
            self._save_library()
            
            self.logger.info(f"Added profile to library: {profile.profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding profile to library: {e}")
            return False
    
    def remove_profile(self, profile_id: str) -> bool:
        """Remove a profile from the library."""
        try:
            if profile_id in self.profiles:
                del self.profiles[profile_id]
                self._save_library()
                self.logger.info(f"Removed profile from library: {profile_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing profile from library: {e}")
            return False
    
    def get_profile(self, profile_id: str) -> Optional[CommunityProfile]:
        """Get a profile from the library."""
        return self.profiles.get(profile_id)
    
    def search_profiles(self, filters: ProfileSearchFilter) -> List[CommunityProfile]:
        """Search profiles in the library with given filters."""
        try:
            results = list(self.profiles.values())
            
            # Apply filters
            if filters.categories:
                results = [p for p in results if p.category in filters.categories]
            
            if filters.difficulties:
                results = [p for p in results if p.difficulty in filters.difficulties]
            
            if filters.tags:
                results = [p for p in results if filters.tags.issubset(set(p.tags))]
            
            if filters.authors:
                results = [p for p in results if p.author in filters.authors]
            
            if filters.min_rating > 0:
                results = [p for p in results if p.rating >= filters.min_rating]
            
            if filters.max_rating < 5.0:
                results = [p for p in results if p.rating <= filters.max_rating]
            
            if filters.min_downloads > 0:
                results = [p for p in results if p.downloads >= filters.min_downloads]
            
            if filters.max_downloads > 0:
                results = [p for p in results if p.downloads <= filters.max_downloads]
            
            if filters.verified_only:
                results = [p for p in results if p.is_verified]
            
            if filters.featured_only:
                results = [p for p in results if p.is_featured]
            
            if filters.compatibility:
                results = [p for p in results if filters.compatibility.intersection(set(p.compatibility))]
            
            if filters.search_text:
                search_lower = filters.search_text.lower()
                results = [p for p in results if 
                          search_lower in p.name.lower() or 
                          search_lower in p.description.lower() or
                          search_lower in p.author.lower()]
            
            # Sort results
            self._sort_profiles(results, filters.sort_order)
            
            # Apply limit
            if filters.limit:
                results = results[:filters.limit]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching profiles: {e}")
            return []
    
    def get_featured_profiles(self) -> List[CommunityProfile]:
        """Get featured profiles from the library."""
        filters = ProfileSearchFilter(featured_only=True)
        return self.search_profiles(filters)
    
    def get_trending_profiles(self, limit: int = 10) -> List[CommunityProfile]:
        """Get trending profiles (most downloaded) from the library."""
        filters = ProfileSearchFilter(
            sort_order=SortOrder.MOST_DOWNLOADED,
            limit=limit
        )
        return self.search_profiles(filters)
    
    def get_categories(self) -> Dict[str, int]:
        """Get available categories with profile counts."""
        return self.metadata.get("categories", {})
    
    def get_tags(self) -> Dict[str, int]:
        """Get available tags with profile counts."""
        return self.metadata.get("tags", {})
    
    def get_authors(self) -> Dict[str, int]:
        """Get available authors with profile counts."""
        return self.metadata.get("authors", {})
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            "total_profiles": len(self.profiles),
            "categories": len(self.get_categories()),
            "tags": len(self.get_tags()),
            "authors": len(self.get_authors()),
            "last_sync": self.metadata.get("last_sync", 0),
            "featured_profiles": len(self.get_featured_profiles())
        }
    
    def _load_library(self):
        """Load the library from disk."""
        try:
            library_file = self.library_path / "library.json"
            if library_file.exists():
                with open(library_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load profiles
                self.profiles = {}
                for profile_data in data.get("profiles", []):
                    try:
                        profile = CommunityProfile.from_dict(profile_data)
                        self.profiles[profile.profile_id] = profile
                    except Exception as e:
                        self.logger.warning(f"Error loading profile: {e}")
                        continue
                
                # Load metadata
                self.metadata = data.get("metadata", self.metadata)
                
                self.logger.info(f"Loaded {len(self.profiles)} profiles from library")
            
        except Exception as e:
            self.logger.error(f"Error loading library: {e}")
    
    def _save_library(self):
        """Save the library to disk."""
        try:
            library_file = self.library_path / "library.json"
            
            data = {
                "profiles": [profile.to_dict() for profile in self.profiles.values()],
                "metadata": self.metadata
            }
            
            with open(library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Library saved to disk")
            
        except Exception as e:
            self.logger.error(f"Error saving library: {e}")
    
    def _update_metadata(self, profile: CommunityProfile):
        """Update library metadata with profile information."""
        # Update category count
        category = profile.category.value
        self.metadata["categories"][category] = self.metadata["categories"].get(category, 0) + 1
        
        # Update tag counts
        for tag in profile.tags:
            self.metadata["tags"][tag] = self.metadata["tags"].get(tag, 0) + 1
        
        # Update author count
        author = profile.author
        self.metadata["authors"][author] = self.metadata["authors"].get(author, 0) + 1
        
        # Update total count
        self.metadata["total_profiles"] = len(self.profiles)
    
    def _sort_profiles(self, profiles: List[CommunityProfile], sort_order: SortOrder):
        """Sort profiles according to the specified order."""
        if sort_order == SortOrder.NEWEST:
            profiles.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_order == SortOrder.OLDEST:
            profiles.sort(key=lambda x: x.created_at)
        elif sort_order == SortOrder.MOST_DOWNLOADED:
            profiles.sort(key=lambda x: x.downloads, reverse=True)
        elif sort_order == SortOrder.LEAST_DOWNLOADED:
            profiles.sort(key=lambda x: x.downloads)
        elif sort_order == SortOrder.HIGHEST_RATED:
            profiles.sort(key=lambda x: x.rating, reverse=True)
        elif sort_order == SortOrder.LOWEST_RATED:
            profiles.sort(key=lambda x: x.rating)
        elif sort_order == SortOrder.ALPHABETICAL:
            profiles.sort(key=lambda x: x.name.lower())
        elif sort_order == SortOrder.REVERSE_ALPHABETICAL:
            profiles.sort(key=lambda x: x.name.lower(), reverse=True)

class ProfileLibraryManager:
    """Manager for profile library operations."""
    
    def __init__(self, library_path: Path, repository_client=None):
        self.library = ProfileLibrary(library_path)
        self.repository_client = repository_client
        self.logger = logging.getLogger(__name__)
    
    def sync_with_repository(self) -> bool:
        """Synchronize local library with remote repository."""
        if not self.repository_client:
            self.logger.warning("No repository client available for sync")
            return False
        
        try:
            # Get all profiles from repository
            filters = {"limit": 1000}  # Get all profiles
            remote_profiles = self.repository_client.search_profiles(filters)
            
            # Update local library
            for profile_data in remote_profiles:
                try:
                    profile = CommunityProfile.from_dict(profile_data)
                    self.library.add_profile(profile)
                except Exception as e:
                    self.logger.warning(f"Error syncing profile: {e}")
                    continue
            
            # Update sync timestamp
            self.library.metadata["last_sync"] = time.time()
            self.library._save_library()
            
            self.logger.info(f"Synced {len(remote_profiles)} profiles from repository")
            return True
            
        except Exception as e:
            self.logger.error(f"Error syncing with repository: {e}")
            return False
    
    def download_profile(self, profile_id: str) -> Optional[CommunityProfile]:
        """Download a profile from the repository and add to local library."""
        if not self.repository_client:
            self.logger.warning("No repository client available for download")
            return None
        
        try:
            # Download from repository
            profile_data = self.repository_client.download_profile(profile_id)
            if not profile_data:
                return None
            
            # Create community profile
            profile = CommunityProfile.from_dict(profile_data)
            
            # Add to local library
            if self.library.add_profile(profile):
                self.logger.info(f"Downloaded and added profile: {profile_id}")
                return profile
            else:
                self.logger.error(f"Failed to add downloaded profile to library: {profile_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading profile: {e}")
            return None
    
    def upload_profile(self, profile: CommunityProfile) -> bool:
        """Upload a profile to the repository."""
        if not self.repository_client:
            self.logger.warning("No repository client available for upload")
            return False
        
        try:
            # Upload to repository
            success = self.repository_client.upload_profile(profile)
            if success:
                # Add to local library
                self.library.add_profile(profile)
                self.logger.info(f"Uploaded profile: {profile.profile_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error uploading profile: {e}")
            return False
    
    def search_profiles(self, filters: ProfileSearchFilter) -> List[CommunityProfile]:
        """Search profiles in the local library."""
        return self.library.search_profiles(filters)
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        return self.library.get_library_stats()
    
    def get_featured_profiles(self) -> List[CommunityProfile]:
        """Get featured profiles from the library."""
        return self.library.get_featured_profiles()
