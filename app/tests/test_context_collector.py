"""Tests for context collector."""

import json
import os
import tempfile
from pathlib import Path

from app.explainer.context_collector import ContextCollector


class TestContextCollector:
    """Test cases for ContextCollector."""

    def test_init(self):
        """Test ContextCollector initialization."""
        collector = ContextCollector("/test/path")
        assert collector.project_path == Path("/test/path").resolve()

    def test_collect_project_context(self):
        """Test collecting project context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = ContextCollector(tmpdir)
            context = collector.collect_project_context()

            # Check all required fields are present
            assert "project_name" in context
            assert "environment" in context
            assert "exposure_level" in context
            assert "tech_stack" in context
            assert "critical_assets" in context
            assert "project_type" in context
            assert "team_size" in context

    def test_get_project_name_from_package_json(self):
        """Test extracting project name from package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text(json.dumps({"name": "test-project"}))

            collector = ContextCollector(tmpdir)
            assert collector._get_project_name() == "test-project"

    def test_get_project_name_from_pyproject_toml(self):
        """Test extracting project name from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pyproject.toml
            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text('[tool.poetry]\nname = "python-project"\nversion = "1.0.0"')

            collector = ContextCollector(tmpdir)
            assert collector._get_project_name() == "python-project"

    def test_get_project_name_from_pom_xml(self):
        """Test extracting project name from pom.xml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pom.xml
            pom_xml = Path(tmpdir) / "pom.xml"
            pom_xml.write_text(
                '<?xml version="1.0"?>\n'
                "<project>\n"
                "  <artifactId>java-project</artifactId>\n"
                "</project>"
            )

            collector = ContextCollector(tmpdir)
            assert collector._get_project_name() == "java-project"

    def test_get_project_name_fallback(self):
        """Test fallback to directory name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = ContextCollector(tmpdir)
            project_name = collector._get_project_name()
            # Should return the directory name
            assert project_name == Path(tmpdir).name

    def test_detect_environment_from_env_vars(self):
        """Test environment detection from environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = ContextCollector(tmpdir)

            # Test production
            os.environ["PRODUCTION_ENV"] = "true"
            assert collector._detect_environment() == "production"
            del os.environ["PRODUCTION_ENV"]

            # Test staging
            os.environ["IS_STAGING"] = "1"
            assert collector._detect_environment() == "staging"
            del os.environ["IS_STAGING"]

    def test_detect_environment_from_env_files(self):
        """Test environment detection from .env files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = ContextCollector(tmpdir)

            # Test production
            env_file = Path(tmpdir) / ".env.production"
            env_file.write_text("DATABASE_URL=prod-db")
            assert collector._detect_environment() == "production"
            env_file.unlink()

            # Test staging
            env_file = Path(tmpdir) / ".env.staging"
            env_file.write_text("API_URL=staging-api")
            assert collector._detect_environment() == "staging"

    def test_analyze_exposure_public(self):
        """Test exposure analysis for public projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create API directory and cloud config
            api_dir = Path(tmpdir) / "api"
            api_dir.mkdir()
            (api_dir / "index.js").write_text("// API endpoint")

            # Create cloud deployment config
            (Path(tmpdir) / "app.yaml").write_text("runtime: nodejs")

            collector = ContextCollector(tmpdir)
            assert collector._analyze_exposure() == "public"

    def test_analyze_exposure_internal(self):
        """Test exposure analysis for internal projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create API and auth directories
            api_dir = Path(tmpdir) / "api"
            api_dir.mkdir()
            (api_dir / "users.py").write_text("# User API")

            auth_dir = Path(tmpdir) / "auth"
            auth_dir.mkdir()
            (auth_dir / "login.py").write_text("# Login logic")

            collector = ContextCollector(tmpdir)
            assert collector._analyze_exposure() == "internal"

    def test_detect_tech_stack(self):
        """Test technology stack detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create various tech indicators
            # Python
            (Path(tmpdir) / "requirements.txt").write_text("django==3.2\npostgresql-driver")
            (Path(tmpdir) / "manage.py").write_text("#!/usr/bin/env python")

            # JavaScript/React
            package_json = {
                "name": "test-app",
                "dependencies": {"react": "^17.0.0", "express": "^4.17.0"},
            }
            (Path(tmpdir) / "package.json").write_text(json.dumps(package_json))

            collector = ContextCollector(tmpdir)
            tech_stack = collector._detect_tech_stack()

            assert "Python" in tech_stack
            assert "JavaScript" in tech_stack
            assert "React" in tech_stack
            assert "Express" in tech_stack
            assert "Django" in tech_stack

    def test_identify_critical_assets(self):
        """Test identification of critical assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create various critical directories
            (Path(tmpdir) / "auth" / "oauth").mkdir(parents=True)
            (Path(tmpdir) / "api" / "v1").mkdir(parents=True)
            (Path(tmpdir) / "payment" / "stripe").mkdir(parents=True)
            (Path(tmpdir) / ".env").write_text("SECRET_KEY=xxx")

            collector = ContextCollector(tmpdir)
            assets = collector._identify_critical_assets()

            assert "認証システム" in assets
            assert "APIエンドポイント" in assets
            assert "決済システム" in assets
            assert "機密情報・設定" in assets

    def test_detect_project_type_web_app(self):
        """Test project type detection for web applications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create web app indicators
            (Path(tmpdir) / "index.html").write_text("<html></html>")
            (Path(tmpdir) / "app.js").write_text("// Main app")
            templates_dir = Path(tmpdir) / "templates"
            templates_dir.mkdir()

            collector = ContextCollector(tmpdir)
            assert collector._detect_project_type() == "Webアプリケーション"

    def test_detect_project_type_api_server(self):
        """Test project type detection for API servers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create API server indicators
            api_dir = Path(tmpdir) / "api" / "v1"
            api_dir.mkdir(parents=True)
            (Path(tmpdir) / "swagger.json").write_text("{}")

            collector = ContextCollector(tmpdir)
            assert collector._detect_project_type() == "APIサーバー"

    def test_detect_project_type_library(self):
        """Test project type detection for libraries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create library indicators
            (Path(tmpdir) / "setup.py").write_text("from setuptools import setup")
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()

            collector = ContextCollector(tmpdir)
            assert collector._detect_project_type() == "ライブラリ/パッケージ"

    def test_estimate_team_size(self):
        """Test team size estimation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Small project
            collector = ContextCollector(tmpdir)
            assert collector._estimate_team_size() == "小規模（1-5人）"

            # Medium project with CODEOWNERS
            (Path(tmpdir) / "CODEOWNERS").write_text("* @team")
            collector = ContextCollector(tmpdir)  # Recreate to pick up new files
            assert collector._estimate_team_size() == "中規模（5-20人）"

            # Large project with CONTRIBUTING.md
            github_dir = Path(tmpdir) / ".github"
            github_dir.mkdir()
            (github_dir / "CONTRIBUTING.md").write_text("# Contributing")
            collector = ContextCollector(tmpdir)  # Recreate to pick up new files
            assert collector._estimate_team_size() == "大規模（20人以上）"
