"""Tests for enhanced prompt templates."""
import pytest

from app.explainer.prompt_templates import (
    get_enhanced_prompt,
    build_analysis_prompt,
    ENHANCED_SECURITY_ANALYSIS_PROMPT,
    SYSTEM_PROMPT_ENHANCED,
    IAM_ANALYSIS_PROMPT_ENHANCED,
    DEPENDENCY_ANALYSIS_PROMPT,
    MULTI_CLOUD_ANALYSIS_PROMPT,
)


class TestPromptTemplates:
    """Test cases for prompt templates."""
    
    def test_enhanced_security_analysis_prompt(self):
        """Test the enhanced security analysis prompt template."""
        assert "クラウドセキュリティとアプリケーションセキュリティの専門家" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{infrastructure_data}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{application_data}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{project_name}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{environment}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{exposure_level}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "{tech_stack}" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "finding_id" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "priority_score" in ENHANCED_SECURITY_ANALYSIS_PROMPT
        assert "compliance_mapping" in ENHANCED_SECURITY_ANALYSIS_PROMPT
    
    def test_system_prompt_enhanced(self):
        """Test the enhanced system prompt."""
        assert "クラウドセキュリティ（AWS, Azure, GCP）" in SYSTEM_PROMPT_ENHANCED
        assert "MITRE ATT&CKフレームワーク" in SYSTEM_PROMPT_ENHANCED
        assert "実用的で、実装可能な推奨事項" in SYSTEM_PROMPT_ENHANCED
    
    def test_iam_analysis_prompt_enhanced(self):
        """Test the enhanced IAM analysis prompt."""
        assert "{iam_data}" in IAM_ANALYSIS_PROMPT_ENHANCED
        assert "{environment}" in IAM_ANALYSIS_PROMPT_ENHANCED
        assert "{exposure_level}" in IAM_ANALYSIS_PROMPT_ENHANCED
        assert "{team_size}" in IAM_ANALYSIS_PROMPT_ENHANCED
        assert "MITRE ATT&CKテクニック" in IAM_ANALYSIS_PROMPT_ENHANCED
        assert "gcloud CLI" in IAM_ANALYSIS_PROMPT_ENHANCED
    
    def test_dependency_analysis_prompt(self):
        """Test the dependency analysis prompt."""
        assert "{vulnerability_data}" in DEPENDENCY_ANALYSIS_PROMPT
        assert "{tech_stack}" in DEPENDENCY_ANALYSIS_PROMPT
        assert "{exposure_level}" in DEPENDENCY_ANALYSIS_PROMPT
        assert "{environment}" in DEPENDENCY_ANALYSIS_PROMPT
        assert "CVE番号とCVSSスコア" in DEPENDENCY_ANALYSIS_PROMPT
        assert "npm/yarn/pip" in DEPENDENCY_ANALYSIS_PROMPT
    
    def test_multi_cloud_analysis_prompt(self):
        """Test the multi-cloud analysis prompt."""
        assert "{cloud_providers}" in MULTI_CLOUD_ANALYSIS_PROMPT
        assert "{security_configs}" in MULTI_CLOUD_ANALYSIS_PROMPT
        assert "クロスクラウドのアクセス管理" in MULTI_CLOUD_ANALYSIS_PROMPT
        assert "統一的なセキュリティポリシー" in MULTI_CLOUD_ANALYSIS_PROMPT
    
    def test_get_enhanced_prompt_security_analysis(self):
        """Test getting enhanced security analysis prompt."""
        context = {
            "project_name": "test-project",
            "environment": "production",
            "exposure_level": "public",
            "tech_stack": ["Python", "GCP"],
            "project_type": "Web Application",
            "critical_assets": ["User Data"]
        }
        
        data = {
            "infrastructure_data": "IAM policies",
            "application_data": "Dependencies"
        }
        
        prompt = get_enhanced_prompt("security_analysis", context, data)
        
        # Check that all placeholders are filled
        assert "test-project" in prompt
        assert "production" in prompt
        assert "public" in prompt
        assert "IAM policies" in prompt
        assert "Dependencies" in prompt
        assert "{" not in prompt  # No unfilled placeholders
    
    def test_get_enhanced_prompt_iam_analysis(self):
        """Test getting enhanced IAM analysis prompt."""
        context = {
            "environment": "staging",
            "exposure_level": "internal",
            "team_size": "中規模（5-20人）"
        }
        
        data = {
            "iam_data": "IAM policy JSON"
        }
        
        prompt = get_enhanced_prompt("iam_analysis", context, data)
        
        assert "staging" in prompt
        assert "internal" in prompt
        assert "中規模（5-20人）" in prompt
        assert "IAM policy JSON" in prompt
    
    def test_get_enhanced_prompt_dependency_analysis(self):
        """Test getting enhanced dependency analysis prompt."""
        context = {
            "tech_stack": "Python, Django",
            "exposure_level": "public",
            "environment": "production"
        }
        
        data = {
            "vulnerability_data": "CVE list"
        }
        
        prompt = get_enhanced_prompt("dependency_analysis", context, data)
        
        assert "Python, Django" in prompt
        assert "public" in prompt
        assert "production" in prompt
        assert "CVE list" in prompt
    
    def test_get_enhanced_prompt_multi_cloud(self):
        """Test getting enhanced multi-cloud prompt."""
        context = {}
        
        data = {
            "cloud_providers": "AWS, GCP, Azure",
            "security_configs": "Security settings"
        }
        
        prompt = get_enhanced_prompt("multi_cloud", context, data)
        
        assert "AWS, GCP, Azure" in prompt
        assert "Security settings" in prompt
    
    def test_get_enhanced_prompt_with_missing_keys(self):
        """Test handling missing keys with defaults."""
        context = {
            "project_name": "test-project"
            # Missing other keys
        }
        
        data = {
            "infrastructure_data": "IAM data"
            # Missing application_data
        }
        
        prompt = get_enhanced_prompt("security_analysis", context, data)
        
        assert "test-project" in prompt
        assert "不明" in prompt  # Default value for missing keys
    
    def test_get_enhanced_prompt_unknown_type(self):
        """Test fallback to default prompt for unknown type."""
        context = {"project_name": "test"}
        data = {"infrastructure_data": "data"}
        
        # Should fall back to security_analysis prompt
        prompt = get_enhanced_prompt("unknown_type", context, data)
        
        assert "クラウドセキュリティとアプリケーションセキュリティの専門家" in prompt
    
    def test_build_analysis_prompt(self):
        """Test building comprehensive analysis prompt."""
        infra_findings = [
            {"title": "IAM Over-privileged", "description": "Owner role assigned"},
            {"title": "Public Storage", "description": "S3 bucket is public"}
        ]
        
        app_findings = [
            {"title": "CVE-2021-1234", "description": "Critical vulnerability in log4j"}
        ]
        
        context = {
            "project_name": "production-api",
            "environment": "production",
            "exposure_level": "public",
            "tech_stack": ["Java", "Spring Boot"],
            "project_type": "API Server",
            "critical_assets": ["Authentication", "User Data"]
        }
        
        prompt = build_analysis_prompt(infra_findings, app_findings, context)
        
        # Check infrastructure findings are included
        assert "IAM Over-privileged: Owner role assigned" in prompt
        assert "Public Storage: S3 bucket is public" in prompt
        
        # Check application findings are included
        assert "CVE-2021-1234: Critical vulnerability in log4j" in prompt
        
        # Check context is included
        assert "production-api" in prompt
        assert "production" in prompt
        assert "public" in prompt
        
        # Check structure
        assert "インフラストラクチャセキュリティ（GCP）" in prompt
        assert "アプリケーションセキュリティ（GitHub Dependabot）" in prompt
    
    def test_build_analysis_prompt_empty_findings(self):
        """Test building prompt with empty findings."""
        infra_findings = []
        app_findings = []
        
        context = {
            "project_name": "test-app",
            "environment": "development"
        }
        
        prompt = build_analysis_prompt(infra_findings, app_findings, context)
        
        assert "なし" in prompt  # Should show "none" for empty findings
        assert "test-app" in prompt