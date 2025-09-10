"""
Community Profile Sharing Module for ZeroLag

This module provides functionality for users to share and import profiles
from a community library, enabling easy access to optimized configurations.

Features:
- Profile upload and download
- Community profile library
- GitHub integration for storage
- Profile rating and review system
- Profile validation and compatibility
- Search and filtering capabilities
"""

from .profile_sharing import (
    ProfileSharingManager,
    ProfileUploader,
    ProfileDownloader,
    CommunityProfile,
    ProfileRating,
    ProfileReview,
    ProfileDifficulty
)

from .github_integration import (
    GitHubProfileRepository,
    GitHubProfileClient,
    ProfileRepositoryConfig
)

from .profile_library import (
    ProfileLibrary,
    ProfileLibraryManager,
    ProfileSearchFilter,
    ProfileCategory,
    SortOrder
)

from .profile_validation import (
    ProfileValidator,
    CompatibilityChecker,
    ProfileValidationResult
)

__all__ = [
    # Core sharing components
    'ProfileSharingManager',
    'ProfileUploader', 
    'ProfileDownloader',
    'CommunityProfile',
    'ProfileRating',
    'ProfileReview',
    'ProfileDifficulty',
    
    # GitHub integration
    'GitHubProfileRepository',
    'GitHubProfileClient',
    'ProfileRepositoryConfig',
    
    # Library management
    'ProfileLibrary',
    'ProfileLibraryManager',
    'ProfileSearchFilter',
    'ProfileCategory',
    'SortOrder',
    
    # Validation
    'ProfileValidator',
    'CompatibilityChecker',
    'ProfileValidationResult'
]
