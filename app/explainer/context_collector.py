"""Context collector for gathering project metadata."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContextCollector:
    """Collect project context information for enhanced security analysis."""

    def __init__(self, project_path: str = "."):
        """Initialize the context collector with a project path."""
        self.project_path = Path(project_path).resolve()

    def collect_project_context(self) -> Dict[str, Any]:
        """
        Collect comprehensive project context information.

        Returns:
            Dictionary containing project metadata
        """
        return {
            "project_name": self._get_project_name(),
            "environment": self._detect_environment(),
            "exposure_level": self._analyze_exposure(),
            "tech_stack": self._detect_tech_stack(),
            "critical_assets": self._identify_critical_assets(),
            "project_type": self._detect_project_type(),
            "team_size": self._estimate_team_size(),
        }

    def _get_project_name(self) -> str:
        """Extract project name from various sources."""
        # Try package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("name", self.project_path.name)
            except Exception as e:
                logger.debug("Failed to parse package.json: %s", e)

        # Try pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, encoding="utf-8") as f:
                    content = f.read()
                    if 'name = "' in content:
                        start = content.find('name = "') + 8
                        end = content.find('"', start)
                        return content[start:end]
            except Exception as e:
                logger.debug("Failed to parse pyproject.toml: %s", e)

        # Try pom.xml for Java projects
        pom_xml = self.project_path / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml, encoding="utf-8") as f:
                    content = f.read()
                    if "<artifactId>" in content:
                        start = content.find("<artifactId>") + 12
                        end = content.find("</artifactId>", start)
                        return content[start:end]
            except Exception as e:
                logger.debug("Failed to parse pom.xml: %s", e)

        # Default to directory name
        return self.project_path.name

    def _detect_environment(self) -> str:
        """Detect the deployment environment."""
        # Check environment variables
        env_indicators = {
            "production": ["PROD", "PRODUCTION", "LIVE"],
            "staging": ["STAGE", "STAGING", "STG"],
            "development": ["DEV", "DEVELOPMENT", "LOCAL"],
        }

        for env_name, indicators in env_indicators.items():
            for indicator in indicators:
                if os.environ.get(f"{indicator}_ENV") or os.environ.get(f"IS_{indicator}"):
                    return env_name

        # Check for .env files
        env_files = {
            "production": [".env.production", ".env.prod"],
            "staging": [".env.staging", ".env.stage"],
            "development": [".env.development", ".env.dev", ".env.local"],
        }

        for env_name, files in env_files.items():
            for file in files:
                if (self.project_path / file).exists():
                    return env_name

        # Check CI/CD configuration
        if (self.project_path / ".github" / "workflows").exists():
            workflows = list((self.project_path / ".github" / "workflows").glob("*.yml"))
            workflows.extend(list((self.project_path / ".github" / "workflows").glob("*.yaml")))
            for workflow in workflows:
                try:
                    with open(workflow, encoding="utf-8") as f:
                        content = f.read().lower()
                        if "production" in content or "deploy" in content:
                            return "production"
                except Exception as e:
                    logger.debug("Failed to read workflow file %s: %s", workflow, e)

        return "development"

    def _analyze_exposure(self) -> str:
        """Analyze the exposure level of the project."""
        # Check for API endpoints
        api_indicators = [
            "**/api/**/*.py",
            "**/api/**/*.js",
            "**/api/**/*.ts",
            "**/routes/**/*.py",
            "**/routes/**/*.js",
            "**/controllers/**/*",
        ]

        has_api = False
        for pattern in api_indicators:
            if list(self.project_path.glob(pattern)):
                has_api = True
                break

        # Check for public cloud configurations
        cloud_configs = [
            "app.yaml",  # Google App Engine
            "serverless.yml",  # Serverless Framework
            "vercel.json",  # Vercel
            "netlify.toml",  # Netlify
        ]

        is_cloud_deployed = any((self.project_path / config).exists() for config in cloud_configs)

        # Check for authentication
        auth_indicators = [
            "**/auth/**/*",
            "**/authentication/**/*",
            "**/login/**/*",
            "**/*auth*.*",
        ]

        has_auth = False
        for pattern in auth_indicators:
            if list(self.project_path.glob(pattern)):
                has_auth = True
                break

        if is_cloud_deployed and has_api:
            return "public"
        if has_api and has_auth:
            return "internal"
        return "private"

    def _detect_tech_stack(self) -> List[str]:
        """Detect the technology stack used in the project."""
        tech_stack = []

        # Detect components
        self._detect_languages(tech_stack)
        self._detect_frameworks(tech_stack)
        self._detect_databases(tech_stack)
        self._detect_cloud_providers(tech_stack)

        return list(set(tech_stack))  # Remove duplicates

    def _detect_languages(self, tech_stack: List[str]) -> None:
        """Detect programming languages used in the project."""
        language_files = {
            "Python": ["*.py", "requirements.txt", "Pipfile", "pyproject.toml"],
            "JavaScript": ["*.js", "package.json"],
            "TypeScript": ["*.ts", "*.tsx", "tsconfig.json"],
            "Java": ["*.java", "pom.xml", "build.gradle"],
            "Go": ["*.go", "go.mod"],
            "Ruby": ["*.rb", "Gemfile"],
            "PHP": ["*.php", "composer.json"],
        }

        for lang, patterns in language_files.items():
            for pattern in patterns:
                if list(self.project_path.rglob(pattern)):
                    tech_stack.append(lang)
                    break

    def _detect_frameworks(self, tech_stack: List[str]) -> None:
        """Detect frameworks used in the project."""
        framework_indicators = {
            "React": ["package.json", "react"],
            "Vue": ["package.json", "vue"],
            "Angular": ["angular.json"],
            "Django": ["manage.py", "django"],
            "Flask": ["flask", "app.py"],
            "FastAPI": ["fastapi", "main.py"],
            "Express": ["package.json", "express"],
            "Spring": ["pom.xml", "spring"],
        }

        for framework, indicators in framework_indicators.items():
            if len(indicators) == 2 and indicators[0] == "package.json":
                if self._check_package_json_dependency(indicators[1]):
                    tech_stack.append(framework)
            else:
                for indicator in indicators:
                    if (self.project_path / indicator).exists():
                        tech_stack.append(framework)
                        break

    def _check_package_json_dependency(self, dependency: str) -> bool:
        """Check if a dependency exists in package.json."""
        pkg_file = self.project_path / "package.json"
        if pkg_file.exists():
            try:
                with open(pkg_file, encoding="utf-8") as f:
                    content = f.read()
                    return dependency in content
            except Exception as e:
                logger.debug("Failed to check package.json dependency: %s", e)
        return False

    def _detect_databases(self, tech_stack: List[str]) -> None:
        """Detect databases used in the project."""
        db_indicators = {
            "PostgreSQL": ["postgres", "postgresql", "psycopg2"],
            "MySQL": ["mysql", "mysqlclient", "pymysql"],
            "MongoDB": ["mongodb", "pymongo", "mongoose"],
            "Redis": ["redis", "redis-py"],
            "SQLite": ["sqlite", "sqlite3"],
        }

        dep_files = ["requirements.txt", "package.json", "pom.xml", "go.mod"]
        for db, indicators in db_indicators.items():
            if self._check_dependencies(indicators, dep_files):
                tech_stack.append(db)

    def _check_dependencies(self, indicators: List[str], dep_files: List[str]) -> bool:
        """Check if any indicator exists in dependency files."""
        for indicator in indicators:
            for dep_file in dep_files:
                file_path = self.project_path / dep_file
                if file_path.exists():
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            if indicator in f.read().lower():
                                return True
                    except Exception as e:
                        logger.debug("Failed to check dependency in %s: %s", dep_file, e)
        return False

    def _detect_cloud_providers(self, tech_stack: List[str]) -> None:
        """Detect cloud providers used in the project."""
        cloud_indicators = {
            "AWS": ["boto3", "aws-sdk", ".aws", "serverless.yml"],
            "GCP": ["google-cloud", "app.yaml", ".gcloud"],
            "Azure": ["azure", ".azure"],
        }

        for cloud, indicators in cloud_indicators.items():
            if self._check_cloud_indicators(indicators, cloud, tech_stack):
                continue

    def _check_cloud_indicators(
        self, indicators: List[str], cloud: str, tech_stack: List[str]
    ) -> bool:
        """Check cloud indicators and add to tech stack if found."""
        for indicator in indicators:
            if indicator.startswith("."):
                if (self.project_path / indicator).exists():
                    tech_stack.append(cloud)
                    return True
            else:
                # Check in dependency files
                for dep_file in ["requirements.txt", "package.json"]:
                    file_path = self.project_path / dep_file
                    if file_path.exists():
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                if indicator in f.read():
                                    tech_stack.append(cloud)
                                    return True
                        except Exception as e:
                            logger.debug("Failed to check cloud indicator in %s: %s", dep_file, e)
        return False

    def _identify_critical_assets(self) -> List[str]:
        """Identify critical assets in the project."""
        critical_assets = []

        # Authentication/Authorization systems
        auth_patterns = [
            "**/auth/**",
            "**/login/**",
            "**/oauth/**",
            "**/jwt/**",
        ]

        for pattern in auth_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("認証システム")
                break

        # API endpoints
        api_patterns = [
            "**/api/**",
            "**/graphql/**",
            "**/rest/**",
        ]

        for pattern in api_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("APIエンドポイント")
                break

        # User data handling
        user_patterns = [
            "**/user/**",
            "**/users/**",
            "**/profile/**",
            "**/account/**",
        ]

        for pattern in user_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("ユーザーデータ")
                break

        # Payment/Financial systems
        payment_patterns = [
            "**/payment/**",
            "**/billing/**",
            "**/stripe/**",
            "**/checkout/**",
        ]

        for pattern in payment_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("決済システム")
                break

        # Database/Data storage
        db_patterns = [
            "**/database/**",
            "**/db/**",
            "**/models/**",
            "**/schema/**",
        ]

        for pattern in db_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("データベース")
                break

        # Secrets/Configuration
        secret_patterns = [
            "**/.env*",
            "**/config/**",
            "**/secrets/**",
            "**/*secret*",
            "**/*key*",
        ]

        for pattern in secret_patterns:
            if list(self.project_path.glob(pattern)):
                critical_assets.append("機密情報・設定")
                break

        return critical_assets if critical_assets else ["特定なし"]

    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        project_type_indicators = {
            "Webアプリケーション": [
                "index.html",
                "app.js",
                "app.py",
                "server.js",
                "server.py",
                "**/templates/**",
                "**/static/**",
                "**/public/**",
            ],
            "APIサーバー": [
                "**/api/**",
                "**/routes/**",
                "**/controllers/**",
                "swagger.json",
                "openapi.yaml",
            ],
            "CLIツール": ["**/cli/**", "**/commands/**", "cli.py", "cli.js"],
            "モバイルアプリ": [
                "AndroidManifest.xml",
                "Info.plist",
                "**/ios/**",
                "**/android/**",
                "react-native",
            ],
        }

        # Check each project type
        for project_type, indicators in project_type_indicators.items():
            if self._check_indicators(indicators):
                return project_type

        # Special case for library/package
        if self._is_library_package():
            return "ライブラリ/パッケージ"

        return "その他"

    def _check_indicators(self, indicators: List[str]) -> bool:
        """Check if any indicator matches for the project."""
        for indicator in indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)):
                    return True
            else:
                if (self.project_path / indicator).exists():
                    return True
        return False

    def _is_library_package(self) -> bool:
        """Check if the project is a library or package."""
        lib_indicators = ["setup.py", "setup.cfg", "lib/**", "src/**"]

        has_main = (
            (self.project_path / "main.py").exists()
            or (self.project_path / "main.js").exists()
            or (self.project_path / "index.js").exists()
        )

        if has_main:
            return False

        return self._check_indicators(lib_indicators)

    def _estimate_team_size(self) -> str:
        """Estimate team size based on git history and project structure."""
        # This is a simplified estimation
        # In a real implementation, you might analyze git history

        # Check for team indicators
        if (self.project_path / ".github" / "CONTRIBUTING.md").exists():
            return "大規模（20人以上）"

        if (self.project_path / "CODEOWNERS").exists():
            return "中規模（5-20人）"

        # Check project complexity
        total_files = len(list(self.project_path.rglob("*")))

        if total_files > 1000:
            return "大規模（20人以上）"
        if total_files > 200:
            return "中規模（5-20人）"
        return "小規模（1-5人）"
