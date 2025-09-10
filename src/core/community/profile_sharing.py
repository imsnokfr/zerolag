"""
Profile Sharing System for ZeroLag

This module implements the core profile sharing functionality including
upload, download, rating, and review systems for community profiles.

Features:
- Profile upload with metadata
- Profile download with validation
- Rating and review system
- Profile search and filtering
- Community profile management
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..profiles.profile import Profile

logger = logging.getLogger(__name__)

class ProfileCategory(Enum):
    """Categories for community profiles."""
    FPS = "fps"
    MOBA = "moba"
    RTS = "rts"
    MMO = "mmo"
    PRODUCTIVITY = "productivity"
    CUSTOM = "custom"
    EXPERIMENTAL = "experimental"

class ProfileDifficulty(Enum):
    """Difficulty levels for profiles."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class ProfileRating:
    """Rating for a community profile."""
    profile_id: str
    user_id: str
    rating: int  # 1-5 stars
    timestamp: float
    comment: Optional[str] = None
    
    def __post_init__(self):
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

@dataclass
class ProfileReview:
    """Detailed review for a community profile."""
    profile_id: str
    user_id: str
    title: str
    content: str
    rating: int
    timestamp: float
    helpful_votes: int = 0
    verified_purchase: bool = False
    
    def __post_init__(self):
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

@dataclass
class CommunityProfile:
    """Community profile with metadata and sharing information."""
    profile_id: str
    name: str
    description: str
    author: str
    author_id: str
    category: ProfileCategory
    difficulty: ProfileDifficulty
    tags: List[str]
    profile_data: Dict[str, Any]
    created_at: float
    updated_at: float
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    reviews: List[ProfileReview] = field(default_factory=list)
    is_verified: bool = False
    is_featured: bool = False
    compatibility: List[str] = field(default_factory=list)  # OS compatibility
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "author_id": self.author_id,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "tags": self.tags,
            "profile_data": self.profile_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "downloads": self.downloads,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "reviews": [self._review_to_dict(r) for r in self.reviews],
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            "compatibility": self.compatibility,
            "requirements": self.requirements
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunityProfile':
        """Create from dictionary."""
        reviews = [cls._review_from_dict(r) for r in data.get("reviews", [])]
        
        return cls(
            profile_id=data["profile_id"],
            name=data["name"],
            description=data["description"],
            author=data["author"],
            author_id=data["author_id"],
            category=ProfileCategory(data["category"]),
            difficulty=ProfileDifficulty(data["difficulty"]),
            tags=data["tags"],
            profile_data=data["profile_data"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0),
            rating_count=data.get("rating_count", 0),
            reviews=reviews,
            is_verified=data.get("is_verified", False),
            is_featured=data.get("is_featured", False),
            compatibility=data.get("compatibility", []),
            requirements=data.get("requirements", {})
        )
    
    @staticmethod
    def _review_to_dict(review: ProfileReview) -> Dict[str, Any]:
        """Convert review to dictionary."""
        return {
            "profile_id": review.profile_id,
            "user_id": review.user_id,
            "title": review.title,
            "content": review.content,
            "rating": review.rating,
            "timestamp": review.timestamp,
            "helpful_votes": review.helpful_votes,
            "verified_purchase": review.verified_purchase
        }
    
    @staticmethod
    def _review_from_dict(data: Dict[str, Any]) -> ProfileReview:
        """Create review from dictionary."""
        return ProfileReview(
            profile_id=data["profile_id"],
            user_id=data["user_id"],
            title=data["title"],
            content=data["content"],
            rating=data["rating"],
            timestamp=data["timestamp"],
            helpful_votes=data.get("helpful_votes", 0),
            verified_purchase=data.get("verified_purchase", False)
        )

class ProfileUploader:
    """Handles uploading profiles to the community library."""
    
    def __init__(self, repository_client):
        self.repository_client = repository_client
        self.logger = logging.getLogger(__name__)
    
    def upload_profile(self, profile: Profile, metadata: Dict[str, Any]) -> str:
        """
        Upload a profile to the community library.
        
        Args:
            profile: The profile to upload
            metadata: Additional metadata (name, description, category, etc.)
            
        Returns:
            The profile ID of the uploaded profile
        """
        try:
            # Generate unique profile ID
            profile_id = self._generate_profile_id(profile, metadata)
            
            # Create community profile
            community_profile = CommunityProfile(
                profile_id=profile_id,
                name=metadata.get("name", profile.name),
                description=metadata.get("description", ""),
                author=metadata.get("author", "Anonymous"),
                author_id=metadata.get("author_id", "anonymous"),
                category=ProfileCategory(metadata.get("category", "custom")),
                difficulty=ProfileDifficulty(metadata.get("difficulty", "intermediate")),
                tags=metadata.get("tags", []),
                profile_data=profile.to_dict(),
                created_at=time.time(),
                updated_at=time.time(),
                compatibility=metadata.get("compatibility", ["windows"]),
                requirements=metadata.get("requirements", {})
            )
            
            # Upload to repository
            success = self.repository_client.upload_profile(community_profile)
            
            if success:
                self.logger.info(f"Successfully uploaded profile: {profile_id}")
                return profile_id
            else:
                raise Exception("Failed to upload profile to repository")
                
        except Exception as e:
            self.logger.error(f"Error uploading profile: {e}")
            raise
    
    def _generate_profile_id(self, profile: Profile, metadata: Dict[str, Any]) -> str:
        """Generate a unique profile ID."""
        # Create a hash based on profile content and metadata
        content = json.dumps(profile.to_dict(), sort_keys=True)
        metadata_str = json.dumps(metadata, sort_keys=True)
        combined = f"{content}:{metadata_str}:{time.time()}"
        
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

class ProfileDownloader:
    """Handles downloading profiles from the community library."""
    
    def __init__(self, repository_client):
        self.repository_client = repository_client
        self.logger = logging.getLogger(__name__)
    
    def download_profile(self, profile_id: str) -> CommunityProfile:
        """
        Download a profile from the community library.
        
        Args:
            profile_id: The ID of the profile to download
            
        Returns:
            The downloaded community profile
        """
        try:
            # Download from repository
            profile_data = self.repository_client.download_profile(profile_id)
            
            if profile_data:
                community_profile = CommunityProfile.from_dict(profile_data)
                
                # Update download count
                self.repository_client.increment_download_count(profile_id)
                
                self.logger.info(f"Successfully downloaded profile: {profile_id}")
                return community_profile
            else:
                raise Exception("Profile not found or download failed")
                
        except Exception as e:
            self.logger.error(f"Error downloading profile: {e}")
            raise
    
    def search_profiles(self, filters: Dict[str, Any]) -> List[CommunityProfile]:
        """
        Search for profiles in the community library.
        
        Args:
            filters: Search filters (category, difficulty, tags, etc.)
            
        Returns:
            List of matching community profiles
        """
        try:
            # Search repository
            profile_data_list = self.repository_client.search_profiles(filters)
            
            profiles = []
            for data in profile_data_list:
                try:
                    profile = CommunityProfile.from_dict(data)
                    profiles.append(profile)
                except Exception as e:
                    self.logger.warning(f"Error parsing profile data: {e}")
                    continue
            
            self.logger.info(f"Found {len(profiles)} profiles matching filters")
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error searching profiles: {e}")
            raise

class ProfileSharingManager:
    """Main manager for profile sharing functionality."""
    
    def __init__(self, repository_client):
        self.uploader = ProfileUploader(repository_client)
        self.downloader = ProfileDownloader(repository_client)
        self.repository_client = repository_client
        self.logger = logging.getLogger(__name__)
    
    def upload_profile(self, profile: Profile, metadata: Dict[str, Any]) -> str:
        """Upload a profile to the community library."""
        return self.uploader.upload_profile(profile, metadata)
    
    def download_profile(self, profile_id: str) -> CommunityProfile:
        """Download a profile from the community library."""
        return self.downloader.download_profile(profile_id)
    
    def search_profiles(self, filters: Dict[str, Any]) -> List[CommunityProfile]:
        """Search for profiles in the community library."""
        return self.downloader.search_profiles(filters)
    
    def rate_profile(self, profile_id: str, user_id: str, rating: int, comment: str = None) -> bool:
        """Rate a community profile."""
        try:
            rating_obj = ProfileRating(
                profile_id=profile_id,
                user_id=user_id,
                rating=rating,
                timestamp=time.time(),
                comment=comment
            )
            
            success = self.repository_client.add_rating(rating_obj)
            if success:
                self.logger.info(f"Successfully rated profile {profile_id} with {rating} stars")
            return success
            
        except Exception as e:
            self.logger.error(f"Error rating profile: {e}")
            return False
    
    def review_profile(self, profile_id: str, user_id: str, title: str, 
                      content: str, rating: int) -> bool:
        """Add a review for a community profile."""
        try:
            review = ProfileReview(
                profile_id=profile_id,
                user_id=user_id,
                title=title,
                content=content,
                rating=rating,
                timestamp=time.time()
            )
            
            success = self.repository_client.add_review(review)
            if success:
                self.logger.info(f"Successfully added review for profile {profile_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding review: {e}")
            return False
    
    def get_profile_stats(self, profile_id: str) -> Dict[str, Any]:
        """Get statistics for a community profile."""
        try:
            return self.repository_client.get_profile_stats(profile_id)
        except Exception as e:
            self.logger.error(f"Error getting profile stats: {e}")
            return {}
    
    def get_featured_profiles(self) -> List[CommunityProfile]:
        """Get featured profiles from the community library."""
        try:
            filters = {"featured": True}
            return self.search_profiles(filters)
        except Exception as e:
            self.logger.error(f"Error getting featured profiles: {e}")
            return []
    
    def get_trending_profiles(self) -> List[CommunityProfile]:
        """Get trending profiles from the community library."""
        try:
            filters = {"sort_by": "downloads", "limit": 10}
            return self.search_profiles(filters)
        except Exception as e:
            self.logger.error(f"Error getting trending profiles: {e}")
            return []
