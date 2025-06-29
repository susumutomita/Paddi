#!/usr/bin/env python3
"""
Code Analyzer Agent

This agent analyzes the actual codebase to find vulnerabilities
and map them to detected security issues.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire
from github import Github, GithubException

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Analyzes codebase for security vulnerabilities and generates fixes."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        local_path: Optional[str] = None,
    ):
        """
        Initialize CodebaseAnalyzer.

        Args:
            github_token: GitHub personal access token
            github_owner: GitHub repository owner
            github_repo: GitHub repository name
            local_path: Path to local repository (alternative to GitHub)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.local_path = local_path

        # Initialize GitHub client if token is provided
        self._github_client = None
        if self.github_token:
            self._github_client = Github(self.github_token)

    def analyze_findings(self, findings_file: str = "data/explained.json") -> List[Dict[str, Any]]:
        """
        Analyze security findings against the actual codebase.

        Args:
            findings_file: Path to the security findings JSON file

        Returns:
            List of findings with code locations and fix suggestions
        """
        # Load security findings
        with open(findings_file, "r", encoding="utf-8") as f:
            findings = json.load(f)

        analyzed_findings = []

        for finding in findings:
            logger.info(f"Analyzing finding: {finding.get('title', 'Unknown')}")

            # Map finding to code locations
            code_locations = self._find_vulnerable_code(finding)

            # Generate fix suggestions for each location
            fix_suggestions = []
            for location in code_locations:
                suggestion = self._generate_fix_suggestion(finding, location)
                if suggestion:
                    fix_suggestions.append(suggestion)

            analyzed_finding = {
                **finding,
                "code_locations": code_locations,
                "fix_suggestions": fix_suggestions,
                "has_code_impact": len(code_locations) > 0,
            }

            analyzed_findings.append(analyzed_finding)

        return analyzed_findings

    def _find_vulnerable_code(self, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find code locations related to a security finding.

        Args:
            finding: Security finding dict

        Returns:
            List of code locations with file paths and line numbers
        """
        locations = []

        # Extract relevant patterns from finding
        patterns = self._extract_search_patterns(finding)

        if self.local_path:
            # Search in local repository
            locations = self._search_local_codebase(patterns)
        elif self._github_client and self.github_owner and self.github_repo:
            # Search in GitHub repository
            locations = self._search_github_codebase(patterns)
        else:
            logger.warning("No codebase source configured (local path or GitHub)")

        return locations

    def _extract_search_patterns(self, finding: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract search patterns from a security finding.

        Args:
            finding: Security finding dict

        Returns:
            List of search patterns with type and pattern
        """
        patterns = []
        title = finding.get("title", "").lower()
        description = finding.get("description", "").lower()

        # IAM/Permission patterns
        if "iam" in title or "permission" in title or "role" in title:
            patterns.extend(
                [
                    {"type": "iam", "pattern": r"roles/owner"},
                    {"type": "iam", "pattern": r"roles/editor"},
                    {"type": "iam", "pattern": r"setIamPolicy"},
                    {"type": "iam", "pattern": r"getIamPolicy"},
                    {"type": "iam", "pattern": r"add_iam_policy_binding"},
                ]
            )

        # Service account patterns
        if "service account" in title or "service account" in description:
            patterns.extend(
                [
                    {"type": "service_account", "pattern": r"\.iam\.gserviceaccount\.com"},
                    {"type": "service_account", "pattern": r"ServiceAccount\("},
                    {"type": "service_account", "pattern": r"service_account_email"},
                    {"type": "service_account", "pattern": r"create_service_account"},
                ]
            )

        # Storage/Bucket patterns
        if "bucket" in title or "storage" in title:
            patterns.extend(
                [
                    {"type": "storage", "pattern": r"storage\.bucket"},
                    {"type": "storage", "pattern": r"bucket\.iam"},
                    {"type": "storage", "pattern": r"publicRead"},
                    {"type": "storage", "pattern": r"allUsers"},
                    {"type": "storage", "pattern": r"bucket_policy"},
                ]
            )

        # XSS/Web vulnerability patterns
        if "xss" in title or "scripting" in title:
            patterns.extend(
                [
                    {"type": "xss", "pattern": r"innerHTML\s*="},
                    {"type": "xss", "pattern": r"document\.write"},
                    {"type": "xss", "pattern": r"eval\("},
                    {"type": "xss", "pattern": r"dangerouslySetInnerHTML"},
                    {"type": "xss", "pattern": r"v-html"},
                ]
            )

        # Container/Docker patterns
        if "container" in title or "docker" in title:
            patterns.extend(
                [
                    {"type": "container", "pattern": r"FROM\s+\w+"},
                    {"type": "container", "pattern": r"Dockerfile"},
                    {"type": "container", "pattern": r"docker-compose"},
                    {"type": "container", "pattern": r"image:\s*[\w/-]+"},
                ]
            )

        return patterns

    def _search_local_codebase(self, patterns: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Search patterns in local codebase."""
        locations = []

        if not self.local_path:
            return locations

        path = Path(self.local_path)

        # Define file extensions to search
        extensions = [".py", ".js", ".ts", ".java", ".go", ".yaml", ".yml", ".json"]

        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            pattern_type = pattern_info["type"]

            # Search files
            for ext in extensions:
                for file_path in path.rglob(f"*{ext}"):
                    if self._should_skip_file(file_path):
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Find all matches
                        for match in re.finditer(pattern, content, re.IGNORECASE):
                            line_num = content[: match.start()].count("\n") + 1

                            locations.append(
                                {
                                    "file": str(file_path.relative_to(path)),
                                    "line": line_num,
                                    "type": pattern_type,
                                    "match": match.group(0),
                                    "context": self._get_context(content, line_num),
                                }
                            )

                    except Exception as e:
                        logger.debug(f"Error reading {file_path}: {e}")

        return locations

    def _search_github_codebase(self, patterns: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Search patterns in GitHub repository."""
        locations = []

        if not all([self._github_client, self.github_owner, self.github_repo]):
            return locations

        try:
            repo = self._github_client.get_repo(f"{self.github_owner}/{self.github_repo}")

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                pattern_type = pattern_info["type"]

                # Use GitHub code search
                query = f"{pattern} repo:{self.github_owner}/{self.github_repo}"

                try:
                    code_results = self._github_client.search_code(query)

                    for code_item in code_results[:10]:  # Limit results
                        file_content = repo.get_contents(code_item.path)

                        if file_content.encoding == "base64":
                            import base64

                            content = base64.b64decode(file_content.content).decode("utf-8")
                        else:
                            content = file_content.decoded_content.decode("utf-8")

                        # Find exact matches in content
                        for match in re.finditer(pattern, content, re.IGNORECASE):
                            line_num = content[: match.start()].count("\n") + 1

                            locations.append(
                                {
                                    "file": code_item.path,
                                    "line": line_num,
                                    "type": pattern_type,
                                    "match": match.group(0),
                                    "context": self._get_context(content, line_num),
                                    "github_url": code_item.html_url,
                                }
                            )

                except Exception as e:
                    logger.debug(f"Error searching pattern '{pattern}': {e}")

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")

        return locations

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}

        for parent in file_path.parents:
            if parent.name in skip_dirs:
                return True

        return False

    def _get_context(self, content: str, line_num: int, context_lines: int = 3) -> str:
        """Get code context around a specific line."""
        lines = content.split("\n")
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)

        context_lines = []
        for i in range(start, end):
            if i == line_num - 1:
                context_lines.append(f">>> {lines[i]}")
            else:
                context_lines.append(f"    {lines[i]}")

        return "\n".join(context_lines)

    def _generate_fix_suggestion(
        self, finding: Dict[str, Any], location: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate fix suggestion for a specific code location.

        Args:
            finding: Security finding
            location: Code location dict

        Returns:
            Fix suggestion dict or None
        """
        suggestion = {
            "file": location["file"],
            "line": location["line"],
            "type": location["type"],
            "severity": finding.get("severity", "MEDIUM"),
        }

        # Generate specific fixes based on vulnerability type
        if location["type"] == "iam":
            suggestion["fix"] = self._generate_iam_fix(location, finding)
        elif location["type"] == "service_account":
            suggestion["fix"] = self._generate_service_account_fix(location, finding)
        elif location["type"] == "storage":
            suggestion["fix"] = self._generate_storage_fix(location, finding)
        elif location["type"] == "xss":
            suggestion["fix"] = self._generate_xss_fix(location, finding)
        elif location["type"] == "container":
            suggestion["fix"] = self._generate_container_fix(location, finding)
        else:
            suggestion["fix"] = {
                "description": "Review this code for security implications",
                "code_change": None,
            }

        return suggestion if suggestion.get("fix") else None

    def _generate_iam_fix(
        self, location: Dict[str, Any], finding: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate IAM-specific fix."""
        match = location["match"]

        if "roles/owner" in match:
            return {
                "description": "Replace owner role with more specific permissions",
                "code_change": match.replace("roles/owner", "roles/editor"),
                "explanation": (
                    "The owner role grants full administrative access. "
                    "Use more specific roles like editor or viewer."
                ),
            }
        elif "roles/editor" in match:
            return {
                "description": "Consider using more restrictive roles",
                "code_change": match.replace("roles/editor", "roles/viewer"),
                "explanation": (
                    "The editor role may be too permissive. "
                    "Consider using viewer or custom roles."
                ),
            }

        return {
            "description": "Review IAM permissions",
            "code_change": None,
            "explanation": finding.get("recommendation", ""),
        }

    def _generate_service_account_fix(
        self, location: Dict[str, Any], finding: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate service account fix."""
        return {
            "description": "Apply principle of least privilege to service account",
            "code_change": None,
            "explanation": (
                "Service accounts should have minimal required permissions. "
                "Consider using workload identity or more specific roles."
            ),
        }

    def _generate_storage_fix(
        self, location: Dict[str, Any], finding: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate storage/bucket fix."""
        match = location["match"]

        if "allUsers" in match or "publicRead" in match:
            return {
                "description": "Remove public access from storage bucket",
                "code_change": match.replace("allUsers", "projectViewer"),
                "explanation": (
                    "Public storage buckets can lead to data exposure. "
                    "Use IAM policies for access control."
                ),
            }

        return {
            "description": "Review storage bucket permissions",
            "code_change": None,
            "explanation": finding.get("recommendation", ""),
        }

    def _generate_xss_fix(
        self, location: Dict[str, Any], finding: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate XSS fix."""
        match = location["match"]

        if "innerHTML" in match:
            return {
                "description": "Use textContent instead of innerHTML",
                "code_change": match.replace("innerHTML", "textContent"),
                "explanation": (
                    "innerHTML can execute scripts. Use textContent for plain text "
                    "or sanitize HTML content."
                ),
            }
        elif "eval(" in match:
            return {
                "description": "Avoid using eval()",
                "code_change": None,
                "explanation": (
                    "eval() executes arbitrary code and is a security risk. "
                    "Use JSON.parse() or safer alternatives."
                ),
            }

        return {
            "description": "Sanitize user input and output",
            "code_change": None,
            "explanation": (
                "Implement proper input validation and output encoding " "to prevent XSS attacks."
            ),
        }

    def _generate_container_fix(
        self, location: Dict[str, Any], finding: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate container/Docker fix."""
        return {
            "description": "Update base image to latest secure version",
            "code_change": None,
            "explanation": (
                "Use specific image tags instead of 'latest' and regularly update "
                "base images for security patches."
            ),
        }

    def save_analysis(
        self, analyzed_findings: List[Dict[str, Any]], output_file: str = "data/code_analysis.json"
    ) -> None:
        """Save code analysis results."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analyzed_findings, f, indent=2, ensure_ascii=False)

        logger.info(f"Code analysis saved to: {output_path}")


def main(
    findings_file: str = "data/explained.json",
    output_file: str = "data/code_analysis.json",
    github_token: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
    local_path: Optional[str] = None,
):
    """
    Analyze codebase for security vulnerabilities.

    Args:
        findings_file: Path to security findings JSON
        output_file: Path to save code analysis results
        github_token: GitHub personal access token
        github_owner: GitHub repository owner
        github_repo: GitHub repository name
        local_path: Path to local repository
    """
    analyzer = CodebaseAnalyzer(
        github_token=github_token,
        github_owner=github_owner,
        github_repo=github_repo,
        local_path=local_path,
    )

    # Analyze findings against codebase
    analyzed_findings = analyzer.analyze_findings(findings_file)

    # Save results
    analyzer.save_analysis(analyzed_findings, output_file)

    # Print summary
    total_findings = len(analyzed_findings)
    code_impacted = sum(1 for f in analyzed_findings if f.get("has_code_impact"))
    total_locations = sum(len(f.get("code_locations", [])) for f in analyzed_findings)

    print("\n✅ Code analysis complete!")
    print(f"   Total findings: {total_findings}")
    print(f"   Findings with code impact: {code_impacted}")
    print(f"   Total code locations found: {total_locations}")
    print(f"   Results saved to: {output_file}")


if __name__ == "__main__":
    fire.Fire(main)
