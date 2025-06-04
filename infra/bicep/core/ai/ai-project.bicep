param account_name string
param location string
param project_name string
param description string  
param display_name string

param aiSearchName string
param cosmosDBName string = ''
param azureStorageName string
param appInsightsName string
param managedIdentityId string
param tags object = {}

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: aiSearchName
}
resource cosmosDBAccount 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' existing = if (!empty(cosmosDBName)) {
  name: cosmosDBName
}
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: azureStorageName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: account_name
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: project_name
  tags: tags
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    description: description
    displayName: display_name
  }

  resource project_connection_cosmosdb_account 'connections@2025-04-01-preview' = if (!empty(cosmosDBName)) {
    name: cosmosDBName
    properties: {
      category: 'CosmosDB'
      target: cosmosDBAccount.properties.documentEndpoint
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiType: 'Azure'
        ResourceId: cosmosDBAccount.id
        location: cosmosDBAccount.location
      }
    }
  }

  resource project_connection_azure_storage 'connections@2025-04-01-preview' = {
    name: azureStorageName
    properties: {
      category: 'AzureStorageAccount'
      target: storageAccount.properties.primaryEndpoints.blob
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiType: 'Azure'
        ResourceId: storageAccount.id
        location: storageAccount.location
      }
    }
  }

  resource project_connection_azureai_search 'connections@2025-04-01-preview' = {
    name: aiSearchName
    properties: {
      category: 'CognitiveSearch'
      target: 'https://${aiSearchName}.search.windows.net'
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiType: 'Azure'
        ResourceId: searchService.id
        location: searchService.location
      }
    }
  }

  // Creates the Azure Foundry connection to your Azure App Insights resource
  resource connection 'connections@2025-04-01-preview' = {
    name: appInsightsName
    properties: {
      category: 'AppInsights'
      target: appInsights.id
      authType: 'ApiKey'
      group: 'ServicesAndApps'
      isSharedToAll: true
      credentials: {
        key: appInsights.properties.ConnectionString
      }
      metadata: {
        ApiType: 'Azure'
        ResourceId: appInsights.id
      }
    }
  }
}

output project_name string = project.name
output project_id string = project.id
output projectPrincipalId string = managedIdentityId
output projectConnectionString string = 'https://${account_name}.services.ai.azure.com/api/projects/${project_name}'

output projectEndpoint string = project.properties.endpoints['AI Foundry API']

#disable-next-line BCP053
output projectWorkspaceId string = project.properties.internalId

// BYO connection names
output cosmosDBConnection string = cosmosDBName
output azureStorageConnection string = azureStorageName
output aiSearchConnection string = aiSearchName
