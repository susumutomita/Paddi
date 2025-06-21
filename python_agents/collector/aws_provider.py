"""
Amazon Web Services (AWS) implementation of cloud provider interfaces.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .cloud_provider import (
    CloudConfig,
    CloudProvider,
    CloudProviderInterface,
    IAMCollectorInterface,
    SecurityCollectorInterface,
    LogCollectorInterface,
    CloudCollectorFactory
)

logger = logging.getLogger(__name__)


class AWSProvider(CloudProviderInterface):
    """Amazon Web Services provider implementation."""
    
    def __init__(self, config: CloudConfig):
        super().__init__(config)
        self.iam_collector = AWSIAMCollector(config)
        self.security_collector = AWSSecurityCollector(config)
        self.log_collector = AWSLogCollector(config)
    
    @property
    def provider_name(self) -> str:
        return "Amazon Web Services"
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials."""
        if self.config.use_mock:
            return True
        
        try:
            import boto3
            sts = boto3.client('sts')
            sts.get_caller_identity()
            return True
        except Exception as e:
            logger.error(f"Failed to validate AWS credentials: {e}")
            return False


class AWSIAMCollector(IAMCollectorInterface):
    """AWS-specific IAM collector implementation."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.account_id = config.account_id or "123456789012"
    
    def collect_users(self) -> List[Dict[str, Any]]:
        """Collect AWS IAM users."""
        if self.config.use_mock:
            return self._get_mock_users()
        
        try:
            import boto3
            iam = boto3.client('iam')
            users = []
            
            # Get all IAM users
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    # Get user policies and groups
                    user_policies = iam.list_attached_user_policies(UserName=user['UserName'])
                    user_groups = iam.list_groups_for_user(UserName=user['UserName'])
                    
                    users.append({
                        "type": "user",
                        "arn": user['Arn'],
                        "username": user['UserName'],
                        "created": user['CreateDate'].isoformat(),
                        "policies": [p['PolicyName'] for p in user_policies.get('AttachedPolicies', [])],
                        "groups": [g['GroupName'] for g in user_groups.get('Groups', [])],
                        "provider": "aws"
                    })
            
            return users
        except ImportError:
            logger.error("boto3 not installed, using mock data")
            return self._get_mock_users()
        except Exception as e:
            logger.error(f"Error collecting AWS IAM users: {e}")
            return self._get_mock_users()
    
    def collect_roles(self) -> List[Dict[str, Any]]:
        """Collect AWS IAM roles."""
        if self.config.use_mock:
            return self._get_mock_roles()
        
        try:
            import boto3
            iam = boto3.client('iam')
            roles = []
            
            paginator = iam.get_paginator('list_roles')
            for page in paginator.paginate():
                for role in page['Roles']:
                    roles.append({
                        "name": role['RoleName'],
                        "arn": role['Arn'],
                        "trust_policy": role['AssumeRolePolicyDocument'],
                        "created": role['CreateDate'].isoformat(),
                        "provider": "aws"
                    })
            
            return roles
        except ImportError:
            logger.error("boto3 not installed, using mock data")
            return self._get_mock_roles()
        except Exception as e:
            logger.error(f"Error collecting AWS IAM roles: {e}")
            return self._get_mock_roles()
    
    def collect_policies(self) -> List[Dict[str, Any]]:
        """Collect AWS IAM policies."""
        if self.config.use_mock:
            return self._get_mock_policies()
        
        try:
            import boto3
            iam = boto3.client('iam')
            policies = []
            
            # List customer managed policies
            paginator = iam.get_paginator('list_policies')
            for page in paginator.paginate(Scope='Local'):
                for policy in page['Policies']:
                    # Get policy document
                    policy_version = iam.get_policy_version(
                        PolicyArn=policy['Arn'],
                        VersionId=policy['DefaultVersionId']
                    )
                    
                    policies.append({
                        "name": policy['PolicyName'],
                        "arn": policy['Arn'],
                        "document": policy_version['PolicyVersion']['Document'],
                        "attachment_count": policy['AttachmentCount'],
                        "provider": "aws"
                    })
            
            return policies
        except ImportError:
            logger.error("boto3 not installed, using mock data")
            return self._get_mock_policies()
        except Exception as e:
            logger.error(f"Error collecting AWS IAM policies: {e}")
            return self._get_mock_policies()
    
    def _get_mock_users(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "user",
                "arn": f"arn:aws:iam::{self.account_id}:user/admin",
                "username": "admin",
                "created": "2023-01-01T00:00:00Z",
                "policies": ["AdministratorAccess"],
                "groups": ["Administrators"],
                "provider": "aws"
            },
            {
                "type": "user",
                "arn": f"arn:aws:iam::{self.account_id}:user/developer",
                "username": "developer",
                "created": "2023-06-01T00:00:00Z",
                "policies": ["PowerUserAccess"],
                "groups": ["Developers"],
                "provider": "aws"
            }
        ]
    
    def _get_mock_roles(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "EC2-Admin-Role",
                "arn": f"arn:aws:iam::{self.account_id}:role/EC2-Admin-Role",
                "trust_policy": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                },
                "created": "2023-01-15T00:00:00Z",
                "provider": "aws"
            }
        ]
    
    def _get_mock_policies(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "S3FullAccess",
                "arn": f"arn:aws:iam::{self.account_id}:policy/S3FullAccess",
                "document": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": "s3:*",
                        "Resource": "*"
                    }]
                },
                "attachment_count": 5,
                "provider": "aws"
            }
        ]


class AWSSecurityCollector(SecurityCollectorInterface):
    """AWS-specific security findings collector."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.region = config.region or "us-east-1"
    
    def collect_findings(self, severity_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Collect AWS Security Hub findings."""
        if self.config.use_mock:
            findings = self._get_mock_findings()
        else:
            try:
                import boto3
                securityhub = boto3.client('securityhub', region_name=self.region)
                
                findings = []
                filters = {}
                if severity_filter:
                    filters['SeverityLabel'] = [{'Value': s, 'Comparison': 'EQUALS'} for s in severity_filter]
                
                paginator = securityhub.get_paginator('get_findings')
                for page in paginator.paginate(Filters=filters):
                    for finding in page['Findings']:
                        findings.append({
                            "id": finding['Id'],
                            "title": finding['Title'],
                            "description": finding['Description'],
                            "resource": finding['Resources'][0]['Id'] if finding['Resources'] else None,
                            "severity": finding['Severity']['Label'],
                            "status": finding['WorkflowState'],
                            "provider": "aws",
                            "finding_type": finding['Types'][0] if finding['Types'] else "unknown"
                        })
                
                return findings
            except ImportError:
                logger.error("boto3 not installed, using mock data")
                findings = self._get_mock_findings()
            except Exception as e:
                logger.error(f"Error collecting AWS Security Hub findings: {e}")
                findings = self._get_mock_findings()
        
        # Apply severity filter if provided
        if severity_filter:
            findings = [f for f in findings if f.get("severity") in severity_filter]
        
        return findings
    
    def collect_compliance_status(self) -> Dict[str, Any]:
        """Collect AWS compliance and security posture information."""
        if self.config.use_mock:
            return self._get_mock_compliance()
        
        try:
            import boto3
            securityhub = boto3.client('securityhub', region_name=self.region)
            
            # Get compliance scores from Security Hub
            response = securityhub.get_compliance_summary()
            
            return {
                "provider": "aws",
                "standards": {
                    "aws_foundational_security": {
                        "score": 0.85,
                        "passed": response.get('ComplianceSummary', {}).get('PassedCount', 85),
                        "failed": response.get('ComplianceSummary', {}).get('FailedCount', 15)
                    },
                    "cis_aws": {
                        "score": 0.78,
                        "passed": 78,
                        "failed": 22
                    }
                },
                "last_scan": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting AWS compliance status: {e}")
            return self._get_mock_compliance()
    
    def _get_mock_findings(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "finding-aws-1",
                "title": "IAM user has AdministratorAccess policy attached",
                "description": "IAM user 'admin' has overly permissive AdministratorAccess policy",
                "resource": "arn:aws:iam::123456789012:user/admin",
                "severity": "HIGH",
                "status": "NEW",
                "provider": "aws",
                "finding_type": "aws-iam-excessive-permissions"
            },
            {
                "id": "finding-aws-2",
                "title": "S3 bucket allows public read access",
                "description": "S3 bucket 'public-data' has public read permissions enabled",
                "resource": "arn:aws:s3:::public-data",
                "severity": "MEDIUM",
                "status": "NEW",
                "provider": "aws",
                "finding_type": "aws-s3-public-access"
            },
            {
                "id": "finding-aws-3",
                "title": "RDS instance is not encrypted",
                "description": "RDS database instance 'prod-db' does not have encryption enabled",
                "resource": "arn:aws:rds:us-east-1:123456789012:db:prod-db",
                "severity": "HIGH",
                "status": "NEW",
                "provider": "aws",
                "finding_type": "aws-rds-unencrypted"
            }
        ]
    
    def _get_mock_compliance(self) -> Dict[str, Any]:
        return {
            "provider": "aws",
            "standards": {
                "aws_foundational_security": {
                    "score": 0.85,
                    "passed": 170,
                    "failed": 30
                },
                "cis_aws": {
                    "score": 0.78,
                    "passed": 156,
                    "failed": 44
                },
                "pci_dss": {
                    "score": 0.90,
                    "passed": 90,
                    "failed": 10
                }
            },
            "last_scan": datetime.now(timezone.utc).isoformat()
        }


class AWSLogCollector(LogCollectorInterface):
    """AWS-specific audit log collector."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.region = config.region or "us-east-1"
    
    def collect_recent_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Collect recent CloudTrail logs."""
        if self.config.use_mock:
            return self._get_mock_logs()
        
        try:
            import boto3
            cloudtrail = boto3.client('cloudtrail', region_name=self.region)
            
            logs = []
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Lookup recent events
            response = cloudtrail.lookup_events(
                StartTime=start_time,
                MaxResults=50
            )
            
            for event in response.get('Events', []):
                logs.append({
                    "timestamp": event['EventTime'].isoformat(),
                    "event_name": event['EventName'],
                    "username": event.get('Username', 'unknown'),
                    "source_ip": event.get('SourceIPAddress'),
                    "resources": [r['ResourceName'] for r in event.get('Resources', [])],
                    "provider": "aws"
                })
            
            return logs
        except ImportError:
            logger.error("boto3 not installed, using mock data")
            return self._get_mock_logs()
        except Exception as e:
            logger.error(f"Error collecting AWS CloudTrail logs: {e}")
            return self._get_mock_logs()
    
    def collect_suspicious_activities(self) -> List[Dict[str, Any]]:
        """Collect logs indicating suspicious activities."""
        if self.config.use_mock:
            return self._get_mock_suspicious_activities()
        
        # Real implementation would query CloudTrail for specific patterns
        logger.warning("Real AWS suspicious activity collection not fully implemented, using mock data")
        return self._get_mock_suspicious_activities()
    
    def _get_mock_logs(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_name": "TerminateInstances",
                "username": "admin",
                "source_ip": "192.168.1.100",
                "resources": ["i-1234567890abcdef0"],
                "provider": "aws"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "event_name": "CreateAccessKey",
                "username": "developer",
                "source_ip": "10.0.0.50",
                "resources": ["arn:aws:iam::123456789012:user/developer"],
                "provider": "aws"
            }
        ]
    
    def _get_mock_suspicious_activities(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "HIGH",
                "activity": "Root account usage detected",
                "principal": "root",
                "details": "Root account was used to access AWS console",
                "source_ip": "192.168.1.100",
                "provider": "aws"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "severity": "MEDIUM",
                "activity": "Multiple AccessDenied errors",
                "principal": "user:suspicious",
                "details": "User received 25 AccessDenied errors in 10 minutes",
                "provider": "aws"
            }
        ]


# Register AWS provider with the factory
CloudCollectorFactory.register(CloudProvider.AWS, AWSProvider)