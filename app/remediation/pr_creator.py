#!/usr/bin/env python3
"""
Pull Request Creator Agent

This agent creates pull requests with security fixes based on code analysis.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import fire
from github import Github, GithubException

logger = logging.getLogger(__name__)


class PullRequestCreator:
    """Creates pull requests with security fixes."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        base_branch: str = "main",
    ):
        """
        Initialize PullRequestCreator.

        Args:
            github_token: GitHub personal access token
            github_owner: GitHub repository owner
            github_repo: GitHub repository name
            base_branch: Base branch for pull requests
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.base_branch = base_branch

        if not self.github_token:
            raise ValueError("GitHub token is required for creating pull requests")

        self._github = Github(self.github_token)
        self._repo = None

    def create_security_fixes_pr(
        self,
        analysis_file: str = "data/code_analysis.json",
        auto_merge: bool = False,
    ) -> Optional[str]:
        """
        Create a pull request with security fixes.

        Args:
            analysis_file: Path to code analysis JSON file
            auto_merge: Whether to auto-merge the PR if checks pass

        Returns:
            Pull request URL or None if no fixes to apply
        """
        # Load code analysis
        with open(analysis_file, "r", encoding="utf-8") as f:
            analyzed_findings = json.load(f)

        # Filter findings with code fixes
        fixable_findings = []
        for finding in analyzed_findings:
            if finding.get("fix_suggestions"):
                for suggestion in finding["fix_suggestions"]:
                    if suggestion.get("fix", {}).get("code_change"):
                        fixable_findings.append({"finding": finding, "suggestion": suggestion})

        if not fixable_findings:
            logger.info("No automated fixes available")
            return None

        # Get repository
        try:
            self._repo = self._github.get_repo(f"{self.github_owner}/{self.github_repo}")
        except GithubException as e:
            logger.error(f"Failed to access repository: {e}")
            return None

        # Create feature branch
        branch_name = f"security-fixes-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            self._create_feature_branch(branch_name)
        except GithubException as e:
            logger.error(f"Failed to create branch: {e}")
            return None

        # Apply fixes
        files_changed = self._apply_fixes(fixable_findings, branch_name)

        if not files_changed:
            logger.warning("No files were changed")
            return None

        # Create pull request
        pr_url = self._create_pull_request(
            branch_name=branch_name,
            findings=fixable_findings,
            files_changed=files_changed,
            auto_merge=auto_merge,
        )

        return pr_url

    def _create_feature_branch(self, branch_name: str) -> None:
        """Create a new feature branch from base branch."""
        base_ref = self._repo.get_git_ref(f"heads/{self.base_branch}")
        base_sha = base_ref.object.sha

        # Create new branch
        self._repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)
        logger.info(f"Created branch: {branch_name}")

    def _apply_fixes(self, fixable_findings: List[Dict[str, Any]], branch_name: str) -> List[str]:
        """
        Apply code fixes to files in the repository.

        Args:
            fixable_findings: List of findings with fixes
            branch_name: Branch to apply fixes to

        Returns:
            List of changed file paths
        """
        files_changed = set()
        file_contents = {}

        # Group fixes by file
        fixes_by_file = {}
        for item in fixable_findings:
            suggestion = item["suggestion"]
            file_path = suggestion["file"]

            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = []
            fixes_by_file[file_path].append(item)

        # Apply fixes to each file
        for file_path, fixes in fixes_by_file.items():
            try:
                # Get current file content
                file_obj = self._repo.get_contents(file_path, ref=branch_name)
                if isinstance(file_obj, list):
                    logger.warning(f"Skipping directory: {file_path}")
                    continue

                content = file_obj.decoded_content.decode("utf-8")
                original_content = content

                # Apply each fix
                for fix_item in fixes:
                    suggestion = fix_item["suggestion"]
                    fix = suggestion["fix"]

                    if fix.get("code_change"):
                        # Simple string replacement
                        old_code = suggestion.get("match", "")
                        new_code = fix["code_change"]

                        if old_code and old_code in content:
                            content = content.replace(old_code, new_code, 1)
                            logger.info(f"Applied fix to {file_path}:{suggestion['line']}")

                # Only update if content changed
                if content != original_content:
                    file_contents[file_path] = {
                        "content": content,
                        "sha": file_obj.sha,
                        "fixes_applied": len(fixes),
                    }
                    files_changed.add(file_path)

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

        # Commit changes
        if file_contents:
            self._commit_changes(file_contents, branch_name)

        return list(files_changed)

    def _commit_changes(self, file_contents: Dict[str, Dict[str, Any]], branch_name: str) -> None:
        """Commit file changes to the branch."""
        commit_message = "fix: Apply automated security fixes\n\n"
        commit_message += "This commit includes the following security fixes:\n"

        for file_path, info in file_contents.items():
            commit_message += f"- {file_path}: {info['fixes_applied']} fix(es) applied\n"

        commit_message += "\nGenerated by Paddi Security Auditor"

        # Update files
        for file_path, info in file_contents.items():
            try:
                self._repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=info["content"],
                    sha=info["sha"],
                    branch=branch_name,
                )
                logger.info(f"Updated file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to update {file_path}: {e}")

    def _create_pull_request(
        self,
        branch_name: str,
        findings: List[Dict[str, Any]],
        files_changed: List[str],
        auto_merge: bool = False,
    ) -> Optional[str]:
        """Create the actual pull request."""
        # Build PR title and body
        title = f"🔒 Security Fixes - {len(findings)} vulnerabilities addressed"

        body = self._generate_pr_body(findings, files_changed)

        try:
            # Create pull request
            pr = self._repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=self.base_branch,
                maintainer_can_modify=True,
            )

            # Add labels
            pr.add_to_labels("security", "automated")

            # Request review if configured
            if os.getenv("GITHUB_REVIEWER"):
                pr.create_review_request(reviewers=[os.getenv("GITHUB_REVIEWER")])

            # Enable auto-merge if requested
            if auto_merge:
                pr.enable_automerge()

            logger.info(f"Created pull request: {pr.html_url}")
            return pr.html_url

        except GithubException as e:
            logger.error(f"Failed to create pull request: {e}")
            return None

    def _generate_pr_body(self, findings: List[Dict[str, Any]], files_changed: List[str]) -> str:
        """Generate pull request description."""
        body = "## 🔒 Automated Security Fixes\n\n"
        body += (
            "This pull request addresses security vulnerabilities detected by "
            "Paddi Security Auditor.\n\n"
        )

        # Summary
        body += "### 📊 Summary\n\n"
        body += f"- **Vulnerabilities addressed**: {len(findings)}\n"
        body += f"- **Files modified**: {len(files_changed)}\n\n"

        # Findings details
        body += "### 🔍 Security Findings Addressed\n\n"

        # Group by severity
        by_severity = {}
        for item in findings:
            finding = item["finding"]
            severity = finding.get("severity", "MEDIUM")
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(item)

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in by_severity:
                body += f"#### {severity} Severity\n\n"
                for item in by_severity[severity]:
                    finding = item["finding"]
                    suggestion = item["suggestion"]

                    body += f"- **{finding['title']}**\n"
                    body += f"  - File: `{suggestion['file']}:{suggestion['line']}`\n"
                    body += f"  - Fix: {suggestion['fix']['description']}\n\n"

        # Files changed
        body += "### 📝 Files Changed\n\n"
        for file_path in sorted(files_changed):
            body += f"- `{file_path}`\n"

        # Testing recommendations
        body += "\n### ✅ Testing Recommendations\n\n"
        body += "Please review and test the following before merging:\n\n"
        body += "1. Run all existing tests to ensure no regressions\n"
        body += "2. Test the specific functionality affected by these changes\n"
        body += "3. Verify that security improvements don't break existing features\n"
        body += "4. Consider adding new tests for the security fixes\n\n"

        # Footer
        body += "---\n"
        body += "*Generated by [Paddi Security Auditor](https://github.com/Sunwood-ai-labs/paddi) "
        body += f"on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return body

    def create_review_comment(
        self, pr_number: int, file_path: str, line: int, comment: str
    ) -> None:
        """Add a review comment to a pull request."""
        try:
            pr = self._repo.get_pull(pr_number)
            pr.create_review_comment(
                body=comment,
                path=file_path,
                line=line,
            )
        except Exception as e:
            logger.error(f"Failed to create review comment: {e}")


def main(
    analysis_file: str = "data/code_analysis.json",
    github_token: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
    base_branch: str = "main",
    auto_merge: bool = False,
):
    """
    Create pull request with security fixes.

    Args:
        analysis_file: Path to code analysis JSON
        github_token: GitHub personal access token
        github_owner: GitHub repository owner
        github_repo: GitHub repository name
        base_branch: Base branch for pull request
        auto_merge: Enable auto-merge if checks pass
    """
    creator = PullRequestCreator(
        github_token=github_token,
        github_owner=github_owner,
        github_repo=github_repo,
        base_branch=base_branch,
    )

    pr_url = creator.create_security_fixes_pr(
        analysis_file=analysis_file,
        auto_merge=auto_merge,
    )

    if pr_url:
        print("\n✅ Pull request created successfully!")
        print(f"   URL: {pr_url}")
    else:
        print("\n❌ No pull request created (no automated fixes available)")


if __name__ == "__main__":
    fire.Fire(main)
