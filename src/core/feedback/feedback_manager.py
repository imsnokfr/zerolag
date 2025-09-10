"""
Feedback Management System for ZeroLag

This module provides comprehensive feedback collection, analysis,
and reporting capabilities for monitoring user feedback and issues.
"""

import json
import time
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging


@dataclass
class FeedbackEntry:
    """Individual feedback entry."""
    feedback_id: str
    timestamp: float
    user_id: str
    feedback_type: str  # bug_report, feature_request, general_feedback, performance_issue
    title: str
    description: str
    severity: str  # low, medium, high, critical
    status: str  # new, in_progress, resolved, closed
    category: str  # gui, performance, input, hotkeys, profiles, etc.
    system_info: Dict[str, Any]
    user_rating: Optional[int] = None  # 1-5 stars
    tags: List[str] = None
    attachments: List[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    resolution_date: Optional[float] = None


@dataclass
class FeedbackStats:
    """Feedback statistics."""
    total_feedback: int
    feedback_by_type: Dict[str, int]
    feedback_by_severity: Dict[str, int]
    feedback_by_status: Dict[str, int]
    feedback_by_category: Dict[str, int]
    average_rating: float
    resolution_rate: float
    average_resolution_time: float
    recent_feedback: List[FeedbackEntry]


class FeedbackManager:
    """Manages user feedback collection and analysis."""
    
    def __init__(self, feedback_dir: str = "logs/feedback"):
        """
        Initialize feedback manager.
        
        Args:
            feedback_dir: Directory to store feedback data
        """
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.feedback_dir / "feedback.json"
        self.stats_file = self.feedback_dir / "feedback_stats.json"
        
        self.feedback_entries: List[FeedbackEntry] = []
        self.load_feedback()
        
        self.logger = logging.getLogger(__name__)
        
        # GitHub integration
        self.github_token = None
        self.github_repo = "imsnokfr/zerolag"
    
    def load_feedback(self):
        """Load existing feedback from file."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_entries = [FeedbackEntry(**entry) for entry in data]
                self.logger.info(f"Loaded {len(self.feedback_entries)} feedback entries")
            except Exception as e:
                self.logger.error(f"Failed to load feedback: {e}")
                self.feedback_entries = []
        else:
            self.feedback_entries = []
    
    def save_feedback(self):
        """Save feedback to file."""
        try:
            data = [asdict(entry) for entry in self.feedback_entries]
            with open(self.feedback_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info("Feedback saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save feedback: {e}")
    
    def add_feedback(self, user_id: str, feedback_type: str, title: str, 
                    description: str, severity: str = "medium", 
                    category: str = "general", user_rating: int = None,
                    tags: List[str] = None, attachments: List[str] = None) -> str:
        """Add new feedback entry."""
        feedback_id = f"feedback_{int(time.time())}_{user_id}"
        
        # Get system information
        system_info = self._get_system_info()
        
        # Create feedback entry
        entry = FeedbackEntry(
            feedback_id=feedback_id,
            timestamp=time.time(),
            user_id=user_id,
            feedback_type=feedback_type,
            title=title,
            description=description,
            severity=severity,
            status="new",
            category=category,
            system_info=system_info,
            user_rating=user_rating,
            tags=tags or [],
            attachments=attachments or []
        )
        
        # Add to entries
        self.feedback_entries.append(entry)
        
        # Save feedback
        self.save_feedback()
        
        # Log feedback
        self.logger.info(f"New feedback added: {feedback_id} - {title}")
        
        # Try to create GitHub issue
        self._create_github_issue(entry)
        
        return feedback_id
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for feedback context."""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "zerolag_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_github_issue(self, entry: FeedbackEntry):
        """Create GitHub issue for feedback."""
        if not self.github_token:
            return
        
        try:
            # Prepare issue data
            issue_data = {
                "title": f"[{entry.feedback_type.upper()}] {entry.title}",
                "body": f"""**Feedback Type:** {entry.feedback_type}
**Severity:** {entry.severity}
**Category:** {entry.category}
**User ID:** {entry.user_id}

**Description:**
{entry.description}

**System Information:**
```json
{json.dumps(entry.system_info, indent=2)}
```

**Tags:** {', '.join(entry.tags) if entry.tags else 'None'}

**Feedback ID:** {entry.feedback_id}
""",
                "labels": [entry.feedback_type, entry.severity, entry.category]
            }
            
            # Create GitHub issue
            response = requests.post(
                f"https://api.github.com/repos/{self.github_repo}/issues",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json=issue_data
            )
            
            if response.status_code == 201:
                issue_info = response.json()
                self.logger.info(f"GitHub issue created: {issue_info['html_url']}")
            else:
                self.logger.warning(f"Failed to create GitHub issue: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error creating GitHub issue: {e}")
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """Get specific feedback entry by ID."""
        for entry in self.feedback_entries:
            if entry.feedback_id == feedback_id:
                return entry
        return None
    
    def update_feedback_status(self, feedback_id: str, status: str, 
                             resolution: str = None, assigned_to: str = None):
        """Update feedback status."""
        entry = self.get_feedback(feedback_id)
        if entry:
            entry.status = status
            if resolution:
                entry.resolution = resolution
                entry.resolution_date = time.time()
            if assigned_to:
                entry.assigned_to = assigned_to
            
            self.save_feedback()
            self.logger.info(f"Updated feedback {feedback_id}: status={status}")
            return True
        return False
    
    def search_feedback(self, query: str = None, feedback_type: str = None,
                       severity: str = None, status: str = None,
                       category: str = None, user_id: str = None) -> List[FeedbackEntry]:
        """Search feedback entries with filters."""
        results = []
        
        for entry in self.feedback_entries:
            # Text search
            if query:
                if query.lower() not in entry.title.lower() and query.lower() not in entry.description.lower():
                    continue
            
            # Filter by type
            if feedback_type and entry.feedback_type != feedback_type:
                continue
            
            # Filter by severity
            if severity and entry.severity != severity:
                continue
            
            # Filter by status
            if status and entry.status != status:
                continue
            
            # Filter by category
            if category and entry.category != category:
                continue
            
            # Filter by user
            if user_id and entry.user_id != user_id:
                continue
            
            results.append(entry)
        
        return results
    
    def get_feedback_stats(self) -> FeedbackStats:
        """Get comprehensive feedback statistics."""
        if not self.feedback_entries:
            return FeedbackStats(
                total_feedback=0,
                feedback_by_type={},
                feedback_by_severity={},
                feedback_by_status={},
                feedback_by_category={},
                average_rating=0.0,
                resolution_rate=0.0,
                average_resolution_time=0.0,
                recent_feedback=[]
            )
        
        # Count by type
        feedback_by_type = {}
        for entry in self.feedback_entries:
            feedback_by_type[entry.feedback_type] = feedback_by_type.get(entry.feedback_type, 0) + 1
        
        # Count by severity
        feedback_by_severity = {}
        for entry in self.feedback_entries:
            feedback_by_severity[entry.severity] = feedback_by_severity.get(entry.severity, 0) + 1
        
        # Count by status
        feedback_by_status = {}
        for entry in self.feedback_entries:
            feedback_by_status[entry.status] = feedback_by_status.get(entry.status, 0) + 1
        
        # Count by category
        feedback_by_category = {}
        for entry in self.feedback_entries:
            feedback_by_category[entry.category] = feedback_by_category.get(entry.category, 0) + 1
        
        # Calculate average rating
        ratings = [entry.user_rating for entry in self.feedback_entries if entry.user_rating]
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Calculate resolution rate
        resolved_count = sum(1 for entry in self.feedback_entries if entry.status in ['resolved', 'closed'])
        resolution_rate = (resolved_count / len(self.feedback_entries)) * 100 if self.feedback_entries else 0.0
        
        # Calculate average resolution time
        resolution_times = []
        for entry in self.feedback_entries:
            if entry.resolution_date and entry.timestamp:
                resolution_times.append(entry.resolution_date - entry.timestamp)
        
        average_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
        
        # Get recent feedback (last 10)
        recent_feedback = sorted(self.feedback_entries, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return FeedbackStats(
            total_feedback=len(self.feedback_entries),
            feedback_by_type=feedback_by_type,
            feedback_by_severity=feedback_by_severity,
            feedback_by_status=feedback_by_status,
            feedback_by_category=feedback_by_category,
            average_rating=average_rating,
            resolution_rate=resolution_rate,
            average_resolution_time=average_resolution_time,
            recent_feedback=recent_feedback
        )
    
    def generate_feedback_report(self) -> str:
        """Generate comprehensive feedback report."""
        stats = self.get_feedback_stats()
        
        report = []
        report.append("ZeroLag Feedback Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Feedback: {stats.total_feedback}")
        report.append("")
        
        # Feedback by type
        report.append("Feedback by Type:")
        report.append("-" * 20)
        for feedback_type, count in stats.feedback_by_type.items():
            report.append(f"  {feedback_type}: {count}")
        report.append("")
        
        # Feedback by severity
        report.append("Feedback by Severity:")
        report.append("-" * 20)
        for severity, count in stats.feedback_by_severity.items():
            report.append(f"  {severity}: {count}")
        report.append("")
        
        # Feedback by status
        report.append("Feedback by Status:")
        report.append("-" * 20)
        for status, count in stats.feedback_by_status.items():
            report.append(f"  {status}: {count}")
        report.append("")
        
        # Feedback by category
        report.append("Feedback by Category:")
        report.append("-" * 20)
        for category, count in stats.feedback_by_category.items():
            report.append(f"  {category}: {count}")
        report.append("")
        
        # Performance metrics
        report.append("Performance Metrics:")
        report.append("-" * 20)
        report.append(f"  Average Rating: {stats.average_rating:.1f}/5.0")
        report.append(f"  Resolution Rate: {stats.resolution_rate:.1f}%")
        report.append(f"  Average Resolution Time: {stats.average_resolution_time/3600:.1f} hours")
        report.append("")
        
        # Recent feedback
        if stats.recent_feedback:
            report.append("Recent Feedback:")
            report.append("-" * 20)
            for entry in stats.recent_feedback[:5]:
                report.append(f"  [{entry.feedback_type}] {entry.title} ({entry.severity})")
                report.append(f"    Status: {entry.status} | Category: {entry.category}")
                report.append(f"    Date: {datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M')}")
                report.append("")
        
        return "\n".join(report)
    
    def export_feedback(self, file_path: str):
        """Export feedback data to file."""
        try:
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_entries": len(self.feedback_entries),
                "feedback_entries": [asdict(entry) for entry in self.feedback_entries],
                "statistics": asdict(self.get_feedback_stats())
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Feedback exported to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export feedback: {e}")
    
    def set_github_token(self, token: str):
        """Set GitHub token for issue creation."""
        self.github_token = token
        self.logger.info("GitHub token set for issue creation")
    
    def get_github_issues(self) -> List[Dict[str, Any]]:
        """Get GitHub issues for the repository."""
        if not self.github_token:
            return []
        
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.github_repo}/issues",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Failed to fetch GitHub issues: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching GitHub issues: {e}")
            return []
