// Assign roles to the service principal 
// NOTE: this requires elevated permissions in the resource group
// Contributor is not enough, you need Owner or User Access Administrator
param registryName string
param storageAccountName string
param keyvaultName string
param openAiName string
param documentIntelligenceName string = ''
param aiSearchName string

param identityPrincipalId string
@allowed(['ServicePrincipal', 'User'])
param principalType string = 'ServicePrincipal'

var roleDefinitions = loadJsonContent('../../data/roleDefinitions.json')

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: registryName
}
resource storage 'Microsoft.Storage/storageAccounts@2022-05-01' existing = {
  name: storageAccountName
}
resource keyvault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyvaultName
}
resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAiName
}
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = if (!empty(documentIntelligenceName)) {
  name: documentIntelligenceName
}
resource aiSearch 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: aiSearchName
}

resource roleAssignmentAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registryName, identityPrincipalId, 'acrPull')
  scope: registry
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.containerregistry.acrPullRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to pull images from the registry ${registryName}'
  }
}

resource roleAssignmentBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registryName, identityPrincipalId, 'blobContributor')
  scope: storage
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.storage.blobDataContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to write to the storage account ${storageAccountName} Blob'
  }
}

resource roleAssignmentTableContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registryName, identityPrincipalId, 'tableContributor')
  scope: storage
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.storage.tableContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to write to the storage account ${storageAccountName} Table'
  }
}

resource roleAssignmentQueueContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registryName, identityPrincipalId, 'queueContributor')
  scope: storage
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.storage.queueDataContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to write to the storage account ${storageAccountName} Queue'
  }
}

// See https://docs.microsoft.com/azure/role-based-access-control/role-assignments-template#new-service-principal
resource managedIdentitycognitiveServicesOpenAIContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesOpenAIContributorRoleId)
  scope: openAi
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesOpenAIContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the OpenAI cognitive services'
  }
}

resource managedIdentitycognitiveServicesDocIntelliOpenAIContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(documentIntelligenceName)) {
  name: guid(
    documentIntelligence.id,
    identityPrincipalId,
    roleDefinitions.openai.cognitiveServicesOpenAIContributorRoleId
  )
  scope: documentIntelligence
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesOpenAIContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the Document Intelligence cognitive services'
  }
}

resource managedIdentitycognitiveServicesUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesUser)
  scope: openAi
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesUser
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the Cognitive Services'
  }
}

resource managedIdentitycognitiveServicesDocIntelliUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(documentIntelligenceName)) {
  name: guid(documentIntelligence.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesUser)
  scope: documentIntelligence
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesUser
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the Document Intelligence'
  }
}

resource managedIdentitycognitiveServicesOpenAiUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesOpenAIUserRoleId)
  scope: openAi
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesOpenAIUserRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} Cognitive Services OpenAI User: Access to OpenAI features - Cognitive Services'
  }
}

resource managedIdentitycognitiveServicesDocIntelliOpenAiUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(documentIntelligenceName)) {
  name: guid(documentIntelligence.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesOpenAIUserRoleId)
  scope: documentIntelligence
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesOpenAIUserRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} Cognitive Services OpenAI User: Access to OpenAI features -  Document Intelligence'
  }
}

resource managedIdentitycognitiveServicesContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesContributorRoleId)
  scope: openAi
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} Cognitive Services Contributor: Full service management for OpenAI'
  }
}

resource managedIdentitycognitiveServicesDocIntelliContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(documentIntelligenceName)) {
  name: guid(documentIntelligence.id, identityPrincipalId, roleDefinitions.openai.cognitiveServicesContributorRoleId)
  scope: documentIntelligence
  properties: {
    principalId: identityPrincipalId
    principalType: principalType
    roleDefinitionId: resourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.openai.cognitiveServicesContributorRoleId
    )
    description: 'Permission for ${principalType} ${identityPrincipalId} Cognitive Services Contributor: Full service management for Document Intelligence'
  }
}

// See https://docs.microsoft.com/azure/role-based-access-control/role-assignments-template#new-service-principal
resource managedIdentitySearchIndexDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiSearch.id, identityPrincipalId, roleDefinitions.search.indexDataContributorRoleId)
  scope: aiSearch
  properties: {
    principalId: identityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.search.indexDataContributorRoleId
    )
    principalType: principalType
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the modify search service indexes'
  }
}

resource managedIdentitySearchIndexDataReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiSearch.id, identityPrincipalId, roleDefinitions.search.indexDataReaderRoleId)
  scope: aiSearch
  properties: {
    principalId: identityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.search.indexDataReaderRoleId
    )
    principalType: principalType
    description: 'Permission for ${principalType} ${identityPrincipalId} to read service indexes'
  }
}

resource managedIdentitySearchServiceContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiSearch.id, identityPrincipalId, roleDefinitions.search.serviceContributorRoleId)
  scope: aiSearch
  properties: {
    principalId: identityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.search.serviceContributorRoleId
    )
    principalType: principalType
    description: 'Permission for ${principalType} ${identityPrincipalId} to use the search service'
  }
}

resource keyVaultContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyvault
  name: guid(resourceGroup().id, identityPrincipalId, roleDefinitions.keyvault.keyVaultContributorRoleId, keyvault.id)
  properties: {
    principalId: identityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.keyvault.keyVaultContributorRoleId
    )
    principalType: principalType
    description: 'Permission for ${principalType} ${identityPrincipalId} to manage the key vault ${keyvault.name}'
  }
}

resource keyVaultSecretOfficerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyvault
  name: guid(resourceGroup().id, identityPrincipalId, roleDefinitions.keyvault.keyVaultSecretOfficerRoleId, keyvault.id)
  properties: {
    principalId: identityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.keyvault.keyVaultSecretOfficerRoleId
    )
    principalType: principalType
    description: 'Permission for ${principalType} ${identityPrincipalId} to use secrets in ${keyvault.name}'
  }
}
