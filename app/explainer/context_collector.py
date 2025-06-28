"""Context collector for gathering project metadata."""
import os
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional


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
                with open(package_json) as f:
                    data = json.load(f)
                    return data.get("name", self.project_path.name)
            except:
                pass
        
        # Try pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject) as f:
                    content = f.read()
                    if 'name = "' in content:
                        start = content.find('name = "') + 8
                        end = content.find('"', start)
                        return content[start:end]
            except:
                pass
        
        # Try pom.xml for Java projects
        pom_xml = self.project_path / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml) as f:
                    content = f.read()
                    if "<artifactId>" in content:
                        start = content.find("<artifactId>") + 12
                        end = content.find("</artifactId>", start)
                        return content[start:end]
            except:
                pass
        
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
                    with open(workflow) as f:
                        content = f.read().lower()
                        if "production" in content or "deploy" in content:
                            return "production"
                except:
                    pass
        
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
        elif has_api and has_auth:
            return "internal"
        else:
            return "private"
    
    def _detect_tech_stack(self) -> List[str]:
        """Detect the technology stack used in the project."""
        tech_stack = []
        
        # Language detection
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
        
        # Framework detection
        framework_indicators = {
            "React": ["package.json", "react"],
            "Vue": ["package.json", "vue"],
            "Angular": ["angular.json"],
            "Django": ["manage.py", "django"],
            "Flask": ["flask", "app.py"],
            "FastAPI": ["fastapi", "main.py"],
            "Express": ["express", "app.js"],
            "Spring": ["pom.xml", "spring"],
        }
        
        for framework, indicators in framework_indicators.items():
            if len(indicators) == 2 and indicators[0] == "package.json":
                pkg_file = self.project_path / "package.json"
                if pkg_file.exists():
                    try:
                        with open(pkg_file) as f:
                            content = f.read()
                            if indicators[1] in content:
                                tech_stack.append(framework)
                    except:
                        pass
            else:
                for indicator in indicators:
                    if (self.project_path / indicator).exists():
                        tech_stack.append(framework)
                        break
        
        # Database detection
        db_indicators = {
            "PostgreSQL": ["postgres", "postgresql", "psycopg2"],
            "MySQL": ["mysql", "mysqlclient", "pymysql"],
            "MongoDB": ["mongodb", "pymongo", "mongoose"],
            "Redis": ["redis", "redis-py"],
            "SQLite": ["sqlite", "sqlite3"],
        }
        
        for db, indicators in db_indicators.items():
            for indicator in indicators:
                # Check in common dependency files
                dep_files = ["requirements.txt", "package.json", "pom.xml", "go.mod"]
                for dep_file in dep_files:
                    file_path = self.project_path / dep_file
                    if file_path.exists():
                        try:
                            with open(file_path) as f:
                                if indicator in f.read().lower():
                                    tech_stack.append(db)
                                    break
                        except:
                            pass
        
        # Cloud provider detection
        cloud_indicators = {
            "AWS": ["boto3", "aws-sdk", ".aws", "serverless.yml"],
            "GCP": ["google-cloud", "app.yaml", ".gcloud"],
            "Azure": ["azure", ".azure"],
        }
        
        for cloud, indicators in cloud_indicators.items():
            for indicator in indicators:
                if indicator.startswith("."):
                    if (self.project_path / indicator).exists():
                        tech_stack.append(cloud)
                        break
                else:
                    # Check in dependency files
                    for dep_file in ["requirements.txt", "package.json"]:
                        file_path = self.project_path / dep_file
                        if file_path.exists():
                            try:
                                with open(file_path) as f:
                                    if indicator in f.read():
                                        tech_stack.append(cloud)
                                        break
                            except:
                                pass
        
        return list(set(tech_stack))  # Remove duplicates
    
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
        # Web application indicators
        web_indicators = [
            "index.html",
            "app.js",
            "app.py",
            "server.js",
            "server.py",
            "**/templates/**",
            "**/static/**",
            "**/public/**",
        ]
        
        for indicator in web_indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)):
                    return "Webアプリケーション"
            else:
                if (self.project_path / indicator).exists():
                    return "Webアプリケーション"
        
        # API server indicators
        api_indicators = [
            "**/api/**",
            "**/routes/**",
            "**/controllers/**",
            "swagger.json",
            "openapi.yaml",
        ]
        
        for indicator in api_indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)):
                    return "APIサーバー"
            else:
                if (self.project_path / indicator).exists():
                    return "APIサーバー"
        
        # Library/Package indicators
        lib_indicators = [
            "setup.py",
            "setup.cfg",
            "lib/**",
            "src/**",
        ]
        
        has_main = (self.project_path / "main.py").exists() or \
                   (self.project_path / "main.js").exists() or \
                   (self.project_path / "index.js").exists()
        
        for indicator in lib_indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)) and not has_main:
                    return "ライブラリ/パッケージ"
            else:
                if (self.project_path / indicator).exists() and not has_main:
                    return "ライブラリ/パッケージ"
        
        # CLI tool indicators
        cli_indicators = [
            "**/cli/**",
            "**/commands/**",
            "cli.py",
            "cli.js",
        ]
        
        for indicator in cli_indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)):
                    return "CLIツール"
            else:
                if (self.project_path / indicator).exists():
                    return "CLIツール"
        
        # Mobile app indicators
        mobile_indicators = [
            "AndroidManifest.xml",
            "Info.plist",
            "**/ios/**",
            "**/android/**",
            "react-native",
        ]
        
        for indicator in mobile_indicators:
            if "*" in indicator:
                if list(self.project_path.glob(indicator)):
                    return "モバイルアプリ"
            else:
                if (self.project_path / indicator).exists():
                    return "モバイルアプリ"
        
        return "その他"
    
    def _estimate_team_size(self) -> str:
        """Estimate team size based on git history and project structure."""
        # This is a simplified estimation
        # In a real implementation, you might analyze git history
        
        # Check for team indicators
        if (self.project_path / "CODEOWNERS").exists():
            return "中規模（5-20人）"
        
        if (self.project_path / ".github" / "CONTRIBUTING.md").exists():
            return "大規模（20人以上）"
        
        # Check project complexity
        total_files = len(list(self.project_path.rglob("*")))
        
        if total_files > 1000:
            return "大規模（20人以上）"
        elif total_files > 200:
            return "中規模（5-20人）"
        else:
            return "小規模（1-5人）"