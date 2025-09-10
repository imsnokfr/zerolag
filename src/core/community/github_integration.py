"""
GitHub Integration for Profile Sharing

This module provides GitHub integration for storing and retrieving
community profiles using GitHub as a backend repository.

Features:
- GitHub API integration
- Profile storage in GitHub repositories
- Profile metadata management
- Search and filtering capabilities
- Rating and review storage
"""

import json
import time
import base64
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import requests
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    requests = None

from .profile_sharing import CommunityProfile, ProfileRating, ProfileReview

logger = logging.getLogger(__name__)

@dataclass
class ProfileRepositoryConfig:
    """Configuration for GitHub profile repository."""
    owner: str
    repo: str
    token: str
    branch: str = "main"
    profiles_path: str = "profiles"
    metadata_path: str = "metadata"
    ratings_path: str = "ratings"
    reviews_path: str = "reviews"

class GitHubProfileClient:
    """GitHub API client for profile operations."""
    
    def __init__(self, config: ProfileRepositoryConfig):
        if not GITHUB_AVAILABLE:
            raise ImportError("requests library is required for GitHub integration")
        
        self.config = config
        self.base_url = f"https://api.github.com/repos/{config.owner}/{config.repo}"
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ZeroLag-ProfileSharing/1.0"
        }
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make a request to the GitHub API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GitHub API request failed: {e}")
            return None
    
    def _get_file_content(self, path: str) -> Optional[str]:
        """Get file content from GitHub repository."""
        try:
            endpoint = f"contents/{path}"
            params = {"ref": self.config.branch}
            
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            if "content" in data:
                # Decode base64 content
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get file content: {e}")
            return None
    
    def _update_file_content(self, path: str, content: str, message: str) -> bool:
        """Update file content in GitHub repository."""
        try:
            # Get current file SHA
            endpoint = f"contents/{path}"
            params = {"ref": self.config.branch}
            
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params
            )
            
            sha = None
            if response.status_code == 200:
                data = response.json()
                sha = data.get("sha")
            
            # Update file
            data = {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": self.config.branch
            }
            
            if sha:
                data["sha"] = sha
            
            response = requests.put(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update file content: {e}")
            return False

class GitHubProfileRepository:
    """GitHub-based profile repository implementation."""
    
    def __init__(self, config: ProfileRepositoryConfig):
        self.config = config
        self.client = GitHubProfileClient(config)
        self.logger = logging.getLogger(__name__)
    
    def upload_profile(self, profile: CommunityProfile) -> bool:
        """Upload a profile to the GitHub repository."""
        try:
            # Upload profile data
            profile_path = f"{self.config.profiles_path}/{profile.profile_id}.json"
            profile_content = json.dumps(profile.to_dict(), indent=2)
            
            success = self.client._update_file_content(
                profile_path,
                profile_content,
                f"Add profile: {profile.name}"
            )
            
            if success:
                # Update metadata index
                self._update_metadata_index(profile)
                self.logger.info(f"Successfully uploaded profile: {profile.profile_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error uploading profile: {e}")
            return False
    
    def download_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Download a profile from the GitHub repository."""
        try:
            profile_path = f"{self.config.profiles_path}/{profile_id}.json"
            content = self.client._get_file_content(profile_path)
            
            if content:
                return json.loads(content)
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading profile: {e}")
            return None
    
    def search_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for profiles in the GitHub repository."""
        try:
            # Get metadata index
            metadata_content = self.client._get_file_content(f"{self.config.metadata_path}/index.json")
            if not metadata_content:
                return []
            
            metadata = json.loads(metadata_content)
            profiles = metadata.get("profiles", [])
            
            # Apply filters
            filtered_profiles = []
            for profile in profiles:
                if self._matches_filters(profile, filters):
                    # Download full profile data
                    full_profile = self.download_profile(profile["profile_id"])
                    if full_profile:
                        filtered_profiles.append(full_profile)
            
            # Sort results
            sort_by = filters.get("sort_by", "created_at")
            reverse = filters.get("reverse", True)
            filtered_profiles.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
            
            # Apply limit
            limit = filters.get("limit")
            if limit:
                filtered_profiles = filtered_profiles[:limit]
            
            return filtered_profiles
            
        except Exception as e:
            self.logger.error(f"Error searching profiles: {e}")
            return []
    
    def add_rating(self, rating: ProfileRating) -> bool:
        """Add a rating to a profile."""
        try:
            ratings_path = f"{self.config.ratings_path}/{rating.profile_id}.json"
            
            # Get existing ratings
            content = self.client._get_file_content(ratings_path)
            ratings = json.loads(content) if content else {"ratings": []}
            
            # Add new rating
            ratings["ratings"].append({
                "user_id": rating.user_id,
                "rating": rating.rating,
                "comment": rating.comment,
                "timestamp": rating.timestamp
            })
            
            # Update average rating
            total_rating = sum(r["rating"] for r in ratings["ratings"])
            ratings["average_rating"] = total_rating / len(ratings["ratings"])
            ratings["rating_count"] = len(ratings["ratings"])
            
            # Save ratings
            success = self.client._update_file_content(
                ratings_path,
                json.dumps(ratings, indent=2),
                f"Add rating for profile {rating.profile_id}"
            )
            
            if success:
                # Update profile metadata
                self._update_profile_rating(rating.profile_id, ratings["average_rating"], ratings["rating_count"])
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding rating: {e}")
            return False
    
    def add_review(self, review: ProfileReview) -> bool:
        """Add a review to a profile."""
        try:
            reviews_path = f"{self.config.reviews_path}/{review.profile_id}.json"
            
            # Get existing reviews
            content = self.client._get_file_content(reviews_path)
            reviews = json.loads(content) if content else {"reviews": []}
            
            # Add new review
            reviews["reviews"].append({
                "user_id": review.user_id,
                "title": review.title,
                "content": review.content,
                "rating": review.rating,
                "timestamp": review.timestamp,
                "helpful_votes": review.helpful_votes,
                "verified_purchase": review.verified_purchase
            })
            
            # Save reviews
            success = self.client._update_file_content(
                reviews_path,
                json.dumps(reviews, indent=2),
                f"Add review for profile {review.profile_id}"
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding review: {e}")
            return False
    
    def increment_download_count(self, profile_id: str) -> bool:
        """Increment the download count for a profile."""
        try:
            # Update metadata index
            metadata_content = self.client._get_file_content(f"{self.config.metadata_path}/index.json")
            if not metadata_content:
                return False
            
            metadata = json.loads(metadata_content)
            profiles = metadata.get("profiles", [])
            
            # Find and update profile
            for profile in profiles:
                if profile["profile_id"] == profile_id:
                    profile["downloads"] = profile.get("downloads", 0) + 1
                    profile["last_downloaded"] = time.time()
                    break
            
            # Save updated metadata
            success = self.client._update_file_content(
                f"{self.config.metadata_path}/index.json",
                json.dumps(metadata, indent=2),
                f"Increment download count for profile {profile_id}"
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error incrementing download count: {e}")
            return False
    
    def get_profile_stats(self, profile_id: str) -> Dict[str, Any]:
        """Get statistics for a profile."""
        try:
            # Get ratings
            ratings_path = f"{self.config.ratings_path}/{profile_id}.json"
            ratings_content = self.client._get_file_content(ratings_path)
            ratings_data = json.loads(ratings_content) if ratings_content else {"ratings": []}
            
            # Get reviews
            reviews_path = f"{self.config.reviews_path}/{profile_id}.json"
            reviews_content = self.client._get_file_content(reviews_path)
            reviews_data = json.loads(reviews_content) if reviews_content else {"reviews": []}
            
            # Get metadata
            metadata_content = self.client._get_file_content(f"{self.config.metadata_path}/index.json")
            metadata = json.loads(metadata_content) if metadata_content else {"profiles": []}
            
            profile_metadata = None
            for profile in metadata.get("profiles", []):
                if profile["profile_id"] == profile_id:
                    profile_metadata = profile
                    break
            
            return {
                "downloads": profile_metadata.get("downloads", 0) if profile_metadata else 0,
                "rating": ratings_data.get("average_rating", 0.0),
                "rating_count": ratings_data.get("rating_count", 0),
                "review_count": len(reviews_data.get("reviews", [])),
                "last_updated": profile_metadata.get("updated_at", 0) if profile_metadata else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting profile stats: {e}")
            return {}
    
    def _update_metadata_index(self, profile: CommunityProfile):
        """Update the metadata index with profile information."""
        try:
            metadata_path = f"{self.config.metadata_path}/index.json"
            
            # Get existing metadata
            content = self.client._get_file_content(metadata_path)
            metadata = json.loads(content) if content else {"profiles": []}
            
            # Add or update profile metadata
            profiles = metadata.get("profiles", [])
            
            # Remove existing entry if present
            profiles = [p for p in profiles if p["profile_id"] != profile.profile_id]
            
            # Add new entry
            profiles.append({
                "profile_id": profile.profile_id,
                "name": profile.name,
                "author": profile.author,
                "category": profile.category.value,
                "difficulty": profile.difficulty.value,
                "tags": profile.tags,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "downloads": profile.downloads,
                "rating": profile.rating,
                "rating_count": profile.rating_count,
                "is_verified": profile.is_verified,
                "is_featured": profile.is_featured,
                "compatibility": profile.compatibility
            })
            
            # Sort by creation date
            profiles.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Save updated metadata
            metadata["profiles"] = profiles
            metadata["last_updated"] = time.time()
            
            self.client._update_file_content(
                metadata_path,
                json.dumps(metadata, indent=2),
                f"Update metadata index for profile {profile.profile_id}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating metadata index: {e}")
    
    def _update_profile_rating(self, profile_id: str, average_rating: float, rating_count: int):
        """Update profile rating in metadata."""
        try:
            metadata_path = f"{self.config.metadata_path}/index.json"
            
            # Get existing metadata
            content = self.client._get_file_content(metadata_path)
            metadata = json.loads(content) if content else {"profiles": []}
            
            # Update profile rating
            profiles = metadata.get("profiles", [])
            for profile in profiles:
                if profile["profile_id"] == profile_id:
                    profile["rating"] = average_rating
                    profile["rating_count"] = rating_count
                    break
            
            # Save updated metadata
            self.client._update_file_content(
                metadata_path,
                json.dumps(metadata, indent=2),
                f"Update rating for profile {profile_id}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating profile rating: {e}")
    
    def _matches_filters(self, profile: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a profile matches the given filters."""
        # Category filter
        if "category" in filters and profile.get("category") != filters["category"]:
            return False
        
        # Difficulty filter
        if "difficulty" in filters and profile.get("difficulty") != filters["difficulty"]:
            return False
        
        # Tags filter
        if "tags" in filters:
            profile_tags = set(profile.get("tags", []))
            filter_tags = set(filters["tags"])
            if not filter_tags.issubset(profile_tags):
                return False
        
        # Author filter
        if "author" in filters and filters["author"].lower() not in profile.get("author", "").lower():
            return False
        
        # Featured filter
        if "featured" in filters and profile.get("is_featured") != filters["featured"]:
            return False
        
        # Verified filter
        if "verified" in filters and profile.get("is_verified") != filters["verified"]:
            return False
        
        # Min rating filter
        if "min_rating" in filters and profile.get("rating", 0) < filters["min_rating"]:
            return False
        
        return True
