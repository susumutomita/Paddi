"""
Microsoft Azure implementation of cloud provider interfaces.
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


class AzureProvider(CloudProviderInterface):
    """Microsoft Azure provider implementation."""
    
    def __init__(self, config: CloudConfig):
        super().__init__(config)
        self.iam_collector = AzureIAMCollector(config)
        self.security_collector = AzureSecurityCollector(config)
        self.log_collector = AzureLogCollector(config)
    
    @property
    def provider_name(self) -> str:
        return "Microsoft Azure"
    
    def validate_credentials(self) -> bool:
        """Validate Azure credentials."""
        if self.config.use_mock:
            return True
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            
            credential = DefaultAzureCredential()
            client = ResourceManagementClient(credential, self.config.subscription_id)
            # Try to list resource groups to validate credentials
            list(client.resource_groups.list())
            return True
        except Exception as e:
            logger.error(f"Failed to validate Azure credentials: {e}")
            return False


class AzureIAMCollector(IAMCollectorInterface):
    """Azure-specific IAM (Azure AD) collector implementation."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.subscription_id = config.subscription_id or "00000000-0000-0000-0000-000000000000"
    
    def collect_users(self) -> List[Dict[str, Any]]:
        """Collect Azure AD users."""
        if self.config.use_mock:
            return self._get_mock_users()
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.graphrbac import GraphRbacManagementClient
            
            credential = DefaultAzureCredential()
            # Note: In production, you'd use Microsoft Graph API instead
            # This is a simplified example
            logger.warning("Real Azure AD user collection requires Microsoft Graph API, using mock data")
            return self._get_mock_users()
        except ImportError:
            logger.error("azure-mgmt libraries not installed, using mock data")
            return self._get_mock_users()
        except Exception as e:
            logger.error(f"Error collecting Azure AD users: {e}")
            return self._get_mock_users()
    
    def collect_roles(self) -> List[Dict[str, Any]]:
        """Collect Azure role definitions."""
        if self.config.use_mock:
            return self._get_mock_roles()
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.authorization import AuthorizationManagementClient
            
            credential = DefaultAzureCredential()
            auth_client = AuthorizationManagementClient(credential, self.subscription_id)
            
            roles = []
            for role in auth_client.role_definitions.list(scope=f"/subscriptions/{self.subscription_id}"):
                roles.append({
                    "name": role.role_name,
                    "id": role.id,
                    "type": role.role_type,
                    "permissions": [
                        {
                            "actions": perm.actions,
                            "not_actions": perm.not_actions,
                            "data_actions": perm.data_actions,
                            "not_data_actions": perm.not_data_actions
                        } for perm in role.permissions
                    ],
                    "assignable_scopes": role.assignable_scopes,
                    "provider": "azure"
                })
            
            return roles
        except ImportError:
            logger.error("azure-mgmt-authorization not installed, using mock data")
            return self._get_mock_roles()
        except Exception as e:
            logger.error(f"Error collecting Azure roles: {e}")
            return self._get_mock_roles()
    
    def collect_policies(self) -> List[Dict[str, Any]]:
        """Collect Azure role assignments and policies."""
        if self.config.use_mock:
            return self._get_mock_policies()
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.authorization import AuthorizationManagementClient
            
            credential = DefaultAzureCredential()
            auth_client = AuthorizationManagementClient(credential, self.subscription_id)
            
            assignments = []
            for assignment in auth_client.role_assignments.list():
                assignments.append({
                    "id": assignment.id,
                    "scope": assignment.scope,
                    "role_definition_id": assignment.role_definition_id,
                    "principal_id": assignment.principal_id,
                    "principal_type": assignment.principal_type,
                    "provider": "azure"
                })
            
            return assignments
        except ImportError:
            logger.error("azure-mgmt-authorization not installed, using mock data")
            return self._get_mock_policies()
        except Exception as e:
            logger.error(f"Error collecting Azure role assignments: {e}")
            return self._get_mock_policies()
    
    def _get_mock_users(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "user",
                "object_id": "11111111-1111-1111-1111-111111111111",
                "user_principal_name": "admin@contoso.onmicrosoft.com",
                "display_name": "Admin User",
                "roles": ["Global Administrator"],
                "provider": "azure"
            },
            {
                "type": "user",
                "object_id": "22222222-2222-2222-2222-222222222222",
                "user_principal_name": "developer@contoso.onmicrosoft.com",
                "display_name": "Developer User",
                "roles": ["Contributor"],
                "provider": "azure"
            },
            {
                "type": "servicePrincipal",
                "object_id": "33333333-3333-3333-3333-333333333333",
                "app_id": "44444444-4444-4444-4444-444444444444",
                "display_name": "MyApp Service Principal",
                "roles": ["Reader"],
                "provider": "azure"
            }
        ]
    
    def _get_mock_roles(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "Owner",
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
                "type": "BuiltInRole",
                "permissions": [{
                    "actions": ["*"],
                    "not_actions": [],
                    "data_actions": ["*"],
                    "not_data_actions": []
                }],
                "assignable_scopes": ["/"],
                "provider": "azure"
            },
            {
                "name": "Contributor",
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
                "type": "BuiltInRole",
                "permissions": [{
                    "actions": ["*"],
                    "not_actions": [
                        "Microsoft.Authorization/*/Delete",
                        "Microsoft.Authorization/*/Write"
                    ],
                    "data_actions": [],
                    "not_data_actions": []
                }],
                "assignable_scopes": ["/"],
                "provider": "azure"
            }
        ]
    
    def _get_mock_policies(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleAssignments/55555555-5555-5555-5555-555555555555",
                "scope": "/subscriptions/00000000-0000-0000-0000-000000000000",
                "role_definition_id": "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
                "principal_id": "11111111-1111-1111-1111-111111111111",
                "principal_type": "User",
                "provider": "azure"
            }
        ]


class AzureSecurityCollector(SecurityCollectorInterface):
    """Azure-specific security findings collector."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.subscription_id = config.subscription_id or "00000000-0000-0000-0000-000000000000"
    
    def collect_findings(self, severity_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Collect Azure Security Center findings."""
        if self.config.use_mock:
            findings = self._get_mock_findings()
        else:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.mgmt.security import SecurityCenter
                
                credential = DefaultAzureCredential()
                security_client = SecurityCenter(credential, self.subscription_id)
                
                findings = []
                for alert in security_client.alerts.list():
                    findings.append({
                        "id": alert.id,
                        "name": alert.name,
                        "description": alert.properties.description,
                        "resource": alert.properties.associated_resource,
                        "severity": alert.properties.severity,
                        "status": alert.properties.status,
                        "provider": "azure",
                        "finding_type": alert.properties.alert_type
                    })
                
                return findings
            except ImportError:
                logger.error("azure-mgmt-security not installed, using mock data")
                findings = self._get_mock_findings()
            except Exception as e:
                logger.error(f"Error collecting Azure Security Center findings: {e}")
                findings = self._get_mock_findings()
        
        # Apply severity filter if provided
        if severity_filter:
            findings = [f for f in findings if f.get("severity") in severity_filter]
        
        return findings
    
    def collect_compliance_status(self) -> Dict[str, Any]:
        """Collect Azure compliance and security posture information."""
        if self.config.use_mock:
            return self._get_mock_compliance()
        
        # Real implementation would use Azure Security Center API
        logger.warning("Real Azure compliance collection not fully implemented, using mock data")
        return self._get_mock_compliance()
    
    def _get_mock_findings(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "finding-azure-1",
                "name": "Excessive permissions for user",
                "description": "User has Global Administrator role which provides excessive permissions",
                "resource": "/subscriptions/00000000-0000-0000-0000-000000000000/users/admin@contoso.onmicrosoft.com",
                "severity": "HIGH",
                "status": "Active",
                "provider": "azure",
                "finding_type": "azure-ad-excessive-permissions"
            },
            {
                "id": "finding-azure-2",
                "name": "Storage account allows public access",
                "description": "Storage account 'publicdata' has public blob access enabled",
                "resource": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/publicdata",
                "severity": "MEDIUM",
                "status": "Active",
                "provider": "azure",
                "finding_type": "azure-storage-public-access"
            },
            {
                "id": "finding-azure-3",
                "name": "SQL Database transparent data encryption disabled",
                "description": "SQL Database 'proddb' does not have transparent data encryption enabled",
                "resource": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Sql/servers/sqlserver1/databases/proddb",
                "severity": "HIGH",
                "status": "Active",
                "provider": "azure",
                "finding_type": "azure-sql-unencrypted"
            }
        ]
    
    def _get_mock_compliance(self) -> Dict[str, Any]:
        return {
            "provider": "azure",
            "standards": {
                "azure_security_benchmark": {
                    "score": 0.82,
                    "passed": 164,
                    "failed": 36
                },
                "cis_azure": {
                    "score": 0.75,
                    "passed": 150,
                    "failed": 50
                },
                "iso_27001": {
                    "score": 0.88,
                    "passed": 88,
                    "failed": 12
                }
            },
            "last_scan": datetime.now(timezone.utc).isoformat()
        }


class AzureLogCollector(LogCollectorInterface):
    """Azure-specific activity log collector."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.subscription_id = config.subscription_id or "00000000-0000-0000-0000-000000000000"
    
    def collect_recent_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Collect recent Azure Activity Logs."""
        if self.config.use_mock:
            return self._get_mock_logs()
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            monitor_client = MonitorManagementClient(credential, self.subscription_id)
            
            logs = []
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Query activity logs
            filter_string = f"eventTimestamp ge '{start_time.isoformat()}'"
            for log in monitor_client.activity_logs.list(filter=filter_string):
                logs.append({
                    "timestamp": log.event_timestamp.isoformat(),
                    "operation": log.operation_name.value,
                    "caller": log.caller,
                    "resource_id": log.resource_id,
                    "status": log.status.value,
                    "provider": "azure"
                })
            
            return logs
        except ImportError:
            logger.error("azure-mgmt-monitor not installed, using mock data")
            return self._get_mock_logs()
        except Exception as e:
            logger.error(f"Error collecting Azure Activity Logs: {e}")
            return self._get_mock_logs()
    
    def collect_suspicious_activities(self) -> List[Dict[str, Any]]:
        """Collect logs indicating suspicious activities."""
        if self.config.use_mock:
            return self._get_mock_suspicious_activities()
        
        # Real implementation would query for specific patterns in Azure logs
        logger.warning("Real Azure suspicious activity collection not fully implemented, using mock data")
        return self._get_mock_suspicious_activities()
    
    def _get_mock_logs(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "Microsoft.Compute/virtualMachines/delete",
                "caller": "admin@contoso.onmicrosoft.com",
                "resource_id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1",
                "status": "Succeeded",
                "provider": "azure"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "operation": "Microsoft.Authorization/roleAssignments/write",
                "caller": "developer@contoso.onmicrosoft.com",
                "resource_id": "/subscriptions/00000000-0000-0000-0000-000000000000",
                "status": "Succeeded",
                "provider": "azure"
            }
        ]
    
    def _get_mock_suspicious_activities(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "HIGH",
                "activity": "Multiple failed login attempts",
                "principal": "suspicious@external.com",
                "details": "15 failed login attempts from different IP addresses",
                "provider": "azure"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "severity": "MEDIUM",
                "activity": "Unusual location access",
                "principal": "user@contoso.onmicrosoft.com",
                "details": "User accessed resources from unusual geographic location",
                "location": "Unknown Country",
                "provider": "azure"
            }
        ]


# Register Azure provider with the factory
CloudCollectorFactory.register(CloudProvider.AZURE, AzureProvider)