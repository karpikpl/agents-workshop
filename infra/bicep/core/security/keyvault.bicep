// --------------------------------------------------------------------------------
// This BICEP file will create a KeyVault
// FYI: To purge a KV with soft delete enabled: > az keyvault purge --name kvName
// --------------------------------------------------------------------------------
param keyVaultName string = ''
param existingKeyVaultName string = ''
param location string = resourceGroup().location
param commonTags object = {}

@description('Administrators that should have access to administer key vault')
param adminUserObjectIds array = []
@description('Application that should have access to read key vault secrets')
param applicationUserObjectIds array = []

@description('Administrator UserId that should have access to administer key vault')
param keyVaultOwnerUserId string = ''
@description('Ip Address of the KV owner so they can read the vault, such as 254.254.254.254/32')
param keyVaultOwnerIpAddress string = ''

@description('Determines if Azure can deploy certificates from this Key Vault.')
param enabledForDeployment bool = true
@description('Determines if templates can reference secrets from this Key Vault.')
param enabledForTemplateDeployment bool = true
@description('Determines if this Key Vault can be used for Azure Disk Encryption.')
param enabledForDiskEncryption bool = true
@description('Determine if soft delete is enabled on this Key Vault.')
param enableSoftDelete bool = true
@description('Determine if purge protection is enabled on this Key Vault.')
param enablePurgeProtection bool = true
@description('The number of days to retain soft deleted vaults and vault objects.')
param softDeleteRetentionInDays int = 7
@description('Determines if access to the objects granted using RBAC. When true, access policies are ignored.')
param useRBAC bool = false
@description('Determines if IAM role assignments should be added to the Key Vault.')
param addRoleAssignments bool = false

@allowed(['Enabled','Disabled'])
param publicNetworkAccess string = 'Enabled'

param privateEndpointSubnetId string = ''
param privateEndpointName string = ''

@description('Create a user assigned identity that can be used to verify and update secrets in future steps')
param createUserAssignedIdentity bool = true
@description('Override the default user assigned identity user name if you need to')
param userAssignedIdentityName string = '${keyVaultName}-cicd'

@description('Create a user assigned identity that DAPR can use to read secrets')
param createDaprIdentity bool = false
@description('Override the default DAPR identity user name if you need to')
param daprIdentityName string = '${keyVaultName}-dapr'

@description('The workspace to store audit logs.')
@metadata({
  strongType: 'Microsoft.OperationalInsights/workspaces'
  example: '/subscriptions/<subscription_id>/resourceGroups/<resource_group>/providers/Microsoft.OperationalInsights/workspaces/<workspace_name>'
})
param workspaceId string = ''

// --------------------------------------------------------------------------------

var useExistingVault = !empty(existingKeyVaultName)

var templateTag = { TemplateFile: '~keyvault.bicep' }
var tags = union(commonTags, templateTag)

var skuName = 'standard'
var subTenantId = subscription().tenantId

var ownerAccessPolicy = keyVaultOwnerUserId == '' ? [] : [
  {
    objectId: keyVaultOwnerUserId
    tenantId: subTenantId
    permissions: {
      certificates: [ 'all' ]
      secrets: [ 'all' ]
      keys: [ 'all' ]
    }
  }
]
var adminAccessPolicies = [for adminUser in adminUserObjectIds: {
  objectId: adminUser.principalId
  tenantId: subTenantId
  permissions: {
    certificates: [ 'all' ]
    secrets: [ 'all' ]
    keys: [ 'all' ]
  }
}]



var applicationUserPolicies = [for appUser in applicationUserObjectIds: {
  objectId: appUser
  tenantId: subTenantId
  permissions: {
    secrets: [ 'get' ]
    keys: [ 'get', 'wrapKey', 'unwrapKey' ] // Azure SQL uses these permissions to access TDE key
  }
}]
var accessPolicies = union(ownerAccessPolicy, adminAccessPolicies, applicationUserPolicies)

var kvIpRules = keyVaultOwnerIpAddress == '' ? [] : [
  {
    value: keyVaultOwnerIpAddress
  }
]

// --------------------------------------------------------------------------------
resource existingKeyVaultResource 'Microsoft.KeyVault/vaults@2021-11-01-preview' existing = if (useExistingVault) {
  name: existingKeyVaultName
}
resource keyVaultResource 'Microsoft.KeyVault/vaults@2021-11-01-preview' = if (!useExistingVault) {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: skuName
    }
    tenantId: subTenantId
    enableRbacAuthorization: useRBAC
    accessPolicies: accessPolicies
    enabledForDeployment: enabledForDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enabledForTemplateDeployment: enabledForTemplateDeployment
    enableSoftDelete: enableSoftDelete
    enablePurgeProtection: enablePurgeProtection // Not allowing to purge key vault or its objects after deletion
    createMode: 'default'                        // Creating or updating the key vault (not recovering)
    softDeleteRetentionInDays: softDeleteRetentionInDays
    publicNetworkAccess: publicNetworkAccess   // Allow access from all networks
    networkAcls: {
      defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny'
      bypass: 'AzureServices'
      ipRules: kvIpRules
      virtualNetworkRules: []
    }
  }
}

// this creates a user assigned identity that can be used to verify and update secrets in future steps
resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' = if (!useExistingVault && createUserAssignedIdentity) {
  name: userAssignedIdentityName
  location: location
}

var userAssignedIdentityPolicies = (!createUserAssignedIdentity) ? [] : [{
  tenantId: userAssignedIdentity.properties.tenantId
  objectId: userAssignedIdentity.properties.principalId
  permissions: {
    secrets: ['get','list','set']
  }
}]

resource userAssignedIdentityAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (createUserAssignedIdentity && addRoleAssignments) {
  scope: keyVaultResource
  name: guid(resourceGroup().id, userAssignedIdentity.id, roleDefinitions.keyvault.keyVaultContributorRoleId, keyVaultResource.id)
  properties: {
    principalId: userAssignedIdentity.properties.principalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.keyvault.keyVaultSecretOfficerRoleId
    )
    principalType: 'ServicePrincipal'
    description: 'Permission for ServicePrincipal ${userAssignedIdentity.properties.principalId} to manage secrets in the key vault ${keyVaultResource.name}'
  }
}

// this creates an identity for DAPR that can be used to get secrets
resource daprIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' = if (!useExistingVault && createDaprIdentity) {
  name: daprIdentityName
  location: location
}
var daprIdentityPolicies = (!createDaprIdentity) ? [] : [{
  tenantId: daprIdentity.properties.tenantId
  objectId: daprIdentity.properties.principalId
  permissions: {
    secrets: ['get','list']
  }
}]

// you can only do one add in a Bicep file, so we union the policies together
var userIdentityPolicies = union(userAssignedIdentityPolicies, daprIdentityPolicies)

resource userAssignedIdentityKeyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2022-07-01' = if (!useExistingVault && (createUserAssignedIdentity || createDaprIdentity)) {
  name: 'add'
  parent: keyVaultResource
  properties: {
    accessPolicies: userIdentityPolicies
  }
}

resource keyVaultAuditLogging 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!useExistingVault && workspaceId != '') {
  name: '${keyVaultResource.name}-auditlogs'
  scope: keyVaultResource
  properties: {
    workspaceId: workspaceId
    logs: [
      {
        category: 'AuditEvent'
        enabled: true
        // Note: Causes error: Diagnostic settings does not support retention for new diagnostic settings.
        // retentionPolicy: {
        //   days: 180
        //   enabled: true
        // }
      }
    ]
  }
}

resource keyVaultMetricLogging 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!useExistingVault && workspaceId != '') {
  name: '${keyVaultResource.name}-metrics'
  scope: keyVaultResource
  properties: {
    workspaceId: workspaceId
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        // Note: Causes error: Diagnostic settings does not support retention for new diagnostic settings.
        // retentionPolicy: {
        //   days: 30
        //   enabled: true
        // }
      }
    ]
  }
}

module privateEndpoint '../networking/private-endpoint.bicep' = if (!useExistingVault && !empty(privateEndpointSubnetId)) {
    name: '${keyVaultName}-private-endpoint'
    params: {
      location: location
      privateEndpointName: privateEndpointName
      groupIds: ['vault']
      targetResourceId: keyVaultResource.id
      subnetId: privateEndpointSubnetId
    }
  }

  var roleDefinitions = loadJsonContent('../../data/roleDefinitions.json')

  resource keyVaultAdminAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for adminUser in adminUserObjectIds: if (!useExistingVault && addRoleAssignments)  {
    scope: keyVaultResource
    name: guid(resourceGroup().id, adminUser.principalId, roleDefinitions.keyvault.keyVaultContributorRoleId, keyVaultResource.id)
    properties: {
      principalId: adminUser.principalId
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        roleDefinitions.keyvault.keyVaultAdministratorRoleId
      )
      principalType: adminUser.principalType
      description: 'Permission for ${adminUser.principalType} ${adminUser.principalId} to administer the key vault ${keyVaultResource.name}'
    }
  }
  ]

  resource keyVaultOwnerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!useExistingVault && addRoleAssignments && !empty(keyVaultOwnerUserId)) {
    scope: keyVaultResource
    name: guid(resourceGroup().id, keyVaultOwnerUserId, roleDefinitions.keyvault.keyVaultContributorRoleId, keyVaultResource.id)
    properties: {
      principalId: keyVaultOwnerUserId
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        roleDefinitions.keyvault.keyVaultAdministratorRoleId
      )
      principalType: 'User'
      description: 'Permission for User ${keyVaultOwnerUserId} to administer the key vault ${keyVaultResource.name}'
    }
  }

// --------------------------------------------------------------------------------
output name string = useExistingVault ? existingKeyVaultResource.name : keyVaultResource.name
output id string = useExistingVault ? existingKeyVaultResource.id : keyVaultResource.id
output userManagedIdentityId string = useExistingVault ? '' : createUserAssignedIdentity ? userAssignedIdentity.id : ''
output endpoint string = useExistingVault ? existingKeyVaultResource.properties.vaultUri : keyVaultResource.properties.vaultUri
output privateEndpointName string = useExistingVault ? '' : privateEndpointName
