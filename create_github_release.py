#!/usr/bin/env python3
"""
ZeroLag GitHub Release Creator

This script creates a GitHub release with the packaged ZeroLag application.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import requests


class GitHubReleaseCreator:
    """Creates GitHub releases for ZeroLag."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.release_dir = self.project_root / "releases"
        self.version = "1.0.0"
        self.repo_owner = "imsnokfr"
        self.repo_name = "zerolag"
        
        # GitHub API configuration
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            print("❌ GITHUB_TOKEN environment variable not set")
            print("Please set your GitHub token: export GITHUB_TOKEN=your_token")
            sys.exit(1)
        
        self.api_base = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_release_notes(self):
        """Get release notes content."""
        release_notes_file = self.release_dir / f"RELEASE_NOTES_v{self.version}.md"
        if release_notes_file.exists():
            with open(release_notes_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"ZeroLag v{self.version} - Gaming Input Optimizer\n\nFirst release of ZeroLag with comprehensive input optimization features."
    
    def create_release(self):
        """Create GitHub release."""
        print("Creating GitHub release...")
        
        release_data = {
            "tag_name": f"v{self.version}",
            "target_commitish": "master",
            "name": f"ZeroLag v{self.version}",
            "body": self.get_release_notes(),
            "draft": False,
            "prerelease": False
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/releases",
                headers=self.headers,
                json=release_data
            )
            response.raise_for_status()
            
            release_info = response.json()
            print(f"✅ Release created: {release_info['html_url']}")
            return release_info
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create release: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None
    
    def upload_assets(self, release_id, upload_url):
        """Upload release assets."""
        print("Uploading release assets...")
        
        # Find executable
        exe_files = []
        for file_path in self.release_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.exe', '.app', '']:
                exe_files.append(file_path)
        
        # Find other important files
        other_files = []
        for file_path in self.release_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.py', '.bat', '.sh']:
                other_files.append(file_path)
        
        all_files = exe_files + other_files
        
        for file_path in all_files:
            if file_path.is_file():
                self.upload_file(file_path, upload_url)
    
    def upload_file(self, file_path, upload_url):
        """Upload a single file to the release."""
        print(f"Uploading: {file_path.name}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                
                response = requests.post(
                    upload_url,
                    headers=self.headers,
                    files=files
                )
                response.raise_for_status()
                
                print(f"✅ Uploaded: {file_path.name}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to upload {file_path.name}: {e}")
    
    def create_zip_package(self):
        """Create a zip package of the release."""
        print("Creating zip package...")
        
        import zipfile
        
        zip_file = self.release_dir / f"ZeroLag_v{self.version}_{self.get_platform()}.zip"
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.release_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.release_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created zip package: {zip_file}")
        return zip_file
    
    def get_platform(self):
        """Get current platform name."""
        import platform
        system = platform.system().lower()
        if system == "windows":
            return "Windows"
        elif system == "darwin":
            return "macOS"
        else:
            return "Linux"
    
    def create_release(self):
        """Create the complete GitHub release."""
        print("=" * 60)
        print("ZeroLag GitHub Release Creator")
        print("=" * 60)
        print(f"Version: {self.version}")
        print(f"Repository: {self.repo_owner}/{self.repo_name}")
        print("")
        
        # Check if release directory exists
        if not self.release_dir.exists():
            print("❌ Release directory not found. Please run build_release.py first.")
            return False
        
        # Create zip package
        zip_file = self.create_zip_package()
        
        # Create GitHub release
        release_info = self.create_release()
        if not release_info:
            return False
        
        # Upload assets
        upload_url = release_info['upload_url'].replace('{?name,label}', '')
        self.upload_assets(release_info['id'], upload_url)
        
        # Upload zip package
        self.upload_file(zip_file, upload_url)
        
        print("")
        print("✅ GitHub release created successfully!")
        print(f"🔗 Release URL: {release_info['html_url']}")
        print("")
        print("Next steps:")
        print("1. Verify the release on GitHub")
        print("2. Test the downloadable files")
        print("3. Announce the release to the community")
        
        return True


def main():
    """Main function."""
    try:
        creator = GitHubReleaseCreator()
        success = creator.create_release()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Release creation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Release creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
