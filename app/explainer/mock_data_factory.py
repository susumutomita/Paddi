"""Mock data factory for consistent test data generation."""

from typing import List

from app.common.models import SecurityFinding


class MockDataFactory:
    """Factory for creating mock security findings."""

    def create_finding(
        self, 
        title: str, 
        severity: str, 
        explanation: str, 
        recommendation: str
    ) -> SecurityFinding:
        """Create a single security finding."""
        return SecurityFinding(
            title=title,
            severity=severity,
            explanation=explanation,
            recommendation=recommendation
        )

    def create_iam_findings(self) -> List[SecurityFinding]:
        """Create generic IAM findings."""
        return [
            self.create_finding(
                title="Overly Permissive Owner Role Assignment",
                severity="HIGH",
                explanation=(
                    "Multiple users have been granted the 'roles/owner' role, "
                    "which provides full administrative access to all resources. "
                    "This violates the principle of least privilege and poses a "
                    "significant security risk."
                ),
                recommendation=(
                    "Remove the owner role from non-essential users. Instead, "
                    "grant specific roles that provide only the necessary "
                    "permissions for their tasks. Consider using roles like "
                    "'roles/editor' or custom roles with limited scope."
                ),
            ),
            self.create_finding(
                title="Service Account with Editor Role",
                severity="MEDIUM",
                explanation=(
                    "The service account 'app-sa@project.iam.gserviceaccount.com' "
                    "has been granted 'roles/editor', which includes broad "
                    "modification permissions across the project."
                ),
                recommendation=(
                    "Replace the editor role with more specific roles that match "
                    "the service account's actual needs. Consider using predefined "
                    "roles like 'roles/storage.objectAdmin' or create a custom "
                    "role with minimal permissions."
                ),
            ),
        ]

    def create_provider_iam_findings(self, provider: str) -> List[SecurityFinding]:
        """Create provider-specific IAM findings."""
        if provider == "aws":
            return self._create_aws_iam_findings()
        elif provider == "azure":
            return self._create_azure_iam_findings()
        elif provider == "gcp":
            return self.create_iam_findings()  # Use generic for GCP
        return []

    def _create_aws_iam_findings(self) -> List[SecurityFinding]:
        """Create AWS-specific IAM findings."""
        return [
            self.create_finding(
                title="AWS IAM User with AdministratorAccess Policy",
                severity="HIGH",
                explanation=(
                    "The IAM user 'admin-user' has the AWS managed policy "
                    "'AdministratorAccess' attached, granting unrestricted access "
                    "to all AWS services and resources. This violates the principle "
                    "of least privilege."
                ),
                recommendation=(
                    "Remove AdministratorAccess policy and create a custom policy "
                    "with only the specific permissions needed. Consider using "
                    "AWS IAM Access Analyzer to identify actual permissions used."
                ),
            ),
            self.create_finding(
                title="EC2 Role with Overly Permissive Assume Role Policy",
                severity="MEDIUM",
                explanation=(
                    "The IAM role 'EC2-Admin-Role' has AdministratorAccess and "
                    "can be assumed by any EC2 instance. This could allow "
                    "compromised instances to gain full AWS access."
                ),
                recommendation=(
                    "Restrict the assume role policy to specific EC2 instances "
                    "or use instance tags. Replace AdministratorAccess with "
                    "minimal required permissions for the workload."
                ),
            ),
        ]

    def _create_azure_iam_findings(self) -> List[SecurityFinding]:
        """Create Azure-specific IAM findings."""
        return [
            self.create_finding(
                title="Azure Subscription Owner Role Assignment",
                severity="HIGH",
                explanation=(
                    "Multiple users have the 'Owner' role at the subscription "
                    "level, providing full control over all resources. This "
                    "creates unnecessary security risk."
                ),
                recommendation=(
                    "Limit Owner role assignments to break-glass accounts only. "
                    "Use more restrictive roles like Contributor or Reader for "
                    "daily operations. Implement Privileged Identity Management "
                    "(PIM) for just-in-time access."
                ),
            ),
            self.create_finding(
                title="Service Principal with Broad Contributor Access",
                severity="MEDIUM",
                explanation=(
                    "The service principal 'Production App' has Contributor "
                    "role across the entire subscription, exceeding its "
                    "operational requirements."
                ),
                recommendation=(
                    "Scope the service principal's permissions to specific "
                    "resource groups or resources. Create custom roles with "
                    "minimal required permissions."
                ),
            ),
        ]

    def create_provider_security_findings(self, provider: str) -> List[SecurityFinding]:
        """Create provider-specific security findings."""
        if provider == "aws":
            return self._create_aws_security_findings()
        elif provider == "azure":
            return self._create_azure_security_findings()
        return []

    def _create_aws_security_findings(self) -> List[SecurityFinding]:
        """Create AWS Security Hub findings."""
        return [
            self.create_finding(
                title="S3 Bucket Allows Public Read Access",
                severity="HIGH",
                explanation=(
                    "AWS Security Hub detected an S3 bucket configured with "
                    "public read access. This violates AWS Foundational "
                    "Security Best Practices and could lead to data exposure."
                ),
                recommendation=(
                    "Disable public access on the S3 bucket immediately. "
                    "Enable S3 Block Public Access at the account level. "
                    "Use CloudFront with signed URLs for controlled public access."
                ),
            ),
            self.create_finding(
                title="RDS Database Instance Lacks Encryption",
                severity="MEDIUM",
                explanation=(
                    "The RDS instance 'production-db' does not have encryption "
                    "at rest enabled, potentially exposing sensitive data if "
                    "the underlying storage is compromised."
                ),
                recommendation=(
                    "Enable encryption for the RDS instance. Create an encrypted "
                    "snapshot and restore to a new encrypted instance. Update "
                    "applications to use the new endpoint."
                ),
            ),
        ]

    def _create_azure_security_findings(self) -> List[SecurityFinding]:
        """Create Azure Security Center findings."""
        return [
            self.create_finding(
                title="Azure Storage Account Allows Public Blob Access",
                severity="HIGH",
                explanation=(
                    "Azure Security Center detected that storage account "
                    "'publicstorageaccount' permits public blob access, "
                    "creating a risk of unauthorized data access."
                ),
                recommendation=(
                    "Disable public blob access on the storage account. "
                    "Implement private endpoints and use SAS tokens for "
                    "controlled access. Enable Azure Defender for Storage."
                ),
            ),
            self.create_finding(
                title="SQL Database Missing Auditing Configuration",
                severity="MEDIUM",
                explanation=(
                    "The Azure SQL Database 'productiondb' lacks auditing "
                    "configuration, limiting visibility into database access "
                    "and potential security incidents."
                ),
                recommendation=(
                    "Enable auditing on the SQL database with Log Analytics "
                    "or Event Hub as destination. Configure audit retention "
                    "per compliance requirements. Set up alerts for suspicious activities."
                ),
            ),
        ]

    def create_scc_findings(self) -> List[SecurityFinding]:
        """Create Security Command Center findings."""
        return [
            self.create_finding(
                title="Over-Privileged Service Account Detected",
                severity="HIGH",
                explanation=(
                    "Security Command Center detected a service account with "
                    "excessive permissions. This account has project-wide access "
                    "that exceeds its operational requirements, creating a "
                    "potential attack vector."
                ),
                recommendation=(
                    "Review and reduce the permissions of the identified service "
                    "account. Implement the principle of least privilege by "
                    "granting only the minimum permissions required for its "
                    "specific functions."
                ),
            ),
            self.create_finding(
                title="Publicly Accessible Storage Bucket",
                severity="MEDIUM",
                explanation=(
                    "A Cloud Storage bucket has been configured with public "
                    "access. This could lead to unintended data exposure if "
                    "sensitive information is stored in this bucket."
                ),
                recommendation=(
                    "Review the bucket's access controls and remove public access "
                    "unless explicitly required. Implement bucket-level IAM "
                    "policies and use signed URLs for temporary access when needed."
                ),
            ),
        ]

    def create_enhanced_findings(self) -> List[SecurityFinding]:
        """Create enhanced findings with Japanese content."""
        return [
            self.create_finding(
                title="過剰な権限を持つサービスアカウント",
                severity="HIGH",
                explanation=(
                    "本番環境のサービスアカウント 'prod-app-sa@project.iam.gserviceaccount.com' が "
                    "Owner権限を持っています。このアカウントが侵害された場合、プロジェクト全体への "
                    "完全なアクセスが可能となり、データ漏洩やサービス停止のリスクがあります。"
                ),
                recommendation=(
                    "最小権限の原則に基づいてロールを見直してください。具体的には：\n"
                    "1. 現在の使用状況を確認: gcloud policy-intelligence query-activity\n"
                    "2. カスタムロールを作成: gcloud iam roles create\n"
                    "3. Owner権限を削除し、必要最小限の権限のみ付与"
                ),
            ),
            self.create_finding(
                title="公開アクセス可能なCloud Storageバケット",
                severity="HIGH",
                explanation=(
                    "'public-data-bucket' が allUsers に対して読み取りアクセスを許可しています。"
                    "機密データが含まれている場合、情報漏洩のリスクがあります。"
                ),
                recommendation=(
                    "バケットの公開アクセスを無効化し、必要に応じて署名付きURLを使用してください。"
                    "コマンド: gsutil iam ch -d allUsers gs://public-data-bucket"
                ),
            ),
        ]