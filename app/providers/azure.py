"""Microsoft Azure provider implementation."""

from typing import Any, Dict, List

from .base import CloudProvider


class AzureProvider(CloudProvider):
    """Microsoft Azure provider implementation."""

    def __init__(self, subscription_id: str = None, tenant_id: str = None, **kwargs):
        """Initialize Azure provider."""
        self.subscription_id = subscription_id or "00000000-0000-0000-0000-000000000000"
        self.tenant_id = tenant_id or "11111111-1111-1111-1111-111111111111"

    def get_name(self) -> str:
        """Return the name of the cloud provider."""
        return "azure"

    def get_iam_policies(self) -> Dict[str, Any]:
        """Retrieve Azure AD roles and permissions."""
        # Mock implementation
        return {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "users": [
                {
                    "displayName": "Admin User",
                    "userPrincipalName": "admin@example.onmicrosoft.com",
                    "id": "user-id-1",
                    "roles": [
                        {
                            "roleDefinitionName": "Owner",
                            "scope": f"/subscriptions/{self.subscription_id}",
                            "roleDefinitionId": (
                                "/providers/Microsoft.Authorization/"
                                "roleDefinitions/owner-role-id"
                            ),
                        }
                    ],
                },
                {
                    "displayName": "Developer User",
                    "userPrincipalName": "developer@example.onmicrosoft.com",
                    "id": "user-id-2",
                    "roles": [
                        {
                            "roleDefinitionName": "Contributor",
                            "scope": f"/subscriptions/{self.subscription_id}",
                            "roleDefinitionId": (
                                "/providers/Microsoft.Authorization/"
                                "roleDefinitions/contributor-role-id"
                            ),
                        }
                    ],
                },
            ],
            "service_principals": [
                {
                    "displayName": "Production App",
                    "appId": "app-id-1",
                    "objectId": "sp-object-id-1",
                    "roles": [
                        {
                            "roleDefinitionName": "Contributor",
                            "scope": (
                                f"/subscriptions/{self.subscription_id}"
                                "/resourceGroups/production"
                            ),
                        }
                    ],
                }
            ],
            "custom_roles": [
                {
                    "roleName": "Custom Admin Role",
                    "id": ("/providers/Microsoft.Authorization/" "roleDefinitions/custom-role-id"),
                    "permissions": [
                        {
                            "actions": ["*"],
                            "notActions": [],
                            "dataActions": ["*"],
                            "notDataActions": [],
                        }
                    ],
                    "assignableScopes": [f"/subscriptions/{self.subscription_id}"],
                }
            ],
        }

    def get_security_findings(self) -> List[Dict[str, Any]]:
        """Retrieve Azure Security Center alerts."""
        # Mock implementation
        return [
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Security/alerts/alert1"
                ),
                "name": "alert1",
                "properties": {
                    "alertDisplayName": "Storage account allows public access",
                    "severity": "High",
                    "status": "Active",
                    "description": (
                        "Storage account 'publicstorageaccount' " "allows public blob access"
                    ),
                    "remediationSteps": [
                        "Navigate to the storage account",
                        "Disable public blob access",
                    ],
                    "affectedResourceType": "Microsoft.Storage/storageAccounts",
                    "affectedResourceName": "publicstorageaccount",
                },
            },
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Security/alerts/alert2"
                ),
                "name": "alert2",
                "properties": {
                    "alertDisplayName": "SQL Database has no auditing enabled",
                    "severity": "Medium",
                    "status": "Active",
                    "description": (
                        "SQL Database 'productiondb' does not " "have auditing enabled"
                    ),
                    "remediationSteps": [
                        "Enable auditing on the SQL database",
                        "Configure audit log retention",
                    ],
                    "affectedResourceType": "Microsoft.Sql/servers/databases",
                    "affectedResourceName": "productiondb",
                },
            },
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Security/alerts/alert3"
                ),
                "name": "alert3",
                "properties": {
                    "alertDisplayName": "Virtual Machine has unmanaged disks",
                    "severity": "Low",
                    "status": "Active",
                    "description": ("Virtual Machine 'legacy-vm' is using " "unmanaged disks"),
                    "remediationSteps": ["Convert unmanaged disks to managed disks"],
                    "affectedResourceType": "Microsoft.Compute/virtualMachines",
                    "affectedResourceName": "legacy-vm",
                },
            },
        ]

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Retrieve Azure Activity Logs."""
        # Mock implementation
        return [
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Insights/eventtypes/management/values/log1"
                ),
                "eventTimestamp": "2024-01-01T10:00:00Z",
                "operationName": {
                    "value": "Microsoft.Authorization/roleAssignments/write",
                    "localizedValue": "Create role assignment",
                },
                "status": {"value": "Succeeded"},
                "caller": "admin@example.onmicrosoft.com",
                "description": "Role assignment created",
                "authorization": {
                    "action": "Microsoft.Authorization/roleAssignments/write",
                    "scope": f"/subscriptions/{self.subscription_id}",
                },
                "properties": {
                    "statusCode": "Created",
                    "serviceRequestId": "request-id-1",
                    "eventCategory": "Administrative",
                },
            },
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Insights/eventtypes/management/values/log2"
                ),
                "eventTimestamp": "2024-01-01T11:00:00Z",
                "operationName": {
                    "value": ("Microsoft.Storage/storageAccounts/" "blobServices/containers/write"),
                    "localizedValue": "Create or Update Blob Container",
                },
                "status": {"value": "Succeeded"},
                "caller": "developer@example.onmicrosoft.com",
                "description": "Blob container created with public access",
                "resourceId": (
                    f"/subscriptions/{self.subscription_id}/resourceGroups/rg1/"
                    "providers/Microsoft.Storage/storageAccounts/"
                    "publicstorageaccount"
                ),
                "properties": {"statusCode": "OK", "serviceRequestId": "request-id-2"},
            },
            {
                "id": (
                    f"/subscriptions/{self.subscription_id}/providers/"
                    "Microsoft.Insights/eventtypes/management/values/log3"
                ),
                "eventTimestamp": "2024-01-01T12:00:00Z",
                "operationName": {
                    "value": "Microsoft.KeyVault/vaults/secrets/write",
                    "localizedValue": "Set Secret",
                },
                "status": {"value": "Succeeded"},
                "caller": "app-id-1",
                "description": "Secret set in Key Vault",
                "resourceId": (
                    f"/subscriptions/{self.subscription_id}/resourceGroups/rg1/"
                    "providers/Microsoft.KeyVault/vaults/prodkeyvault"
                ),
                "properties": {"statusCode": "OK", "serviceRequestId": "request-id-3"},
            },
        ]

    def collect_all(self) -> Dict[str, Any]:
        """Collect all Azure security data."""
        return {
            "provider": self.get_name(),
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "iam_policies": self.get_iam_policies(),
            "security_findings": self.get_security_findings(),
            "audit_logs": self.get_audit_logs(),
        }
