targetScope = 'resourceGroup'

@description('Environment name used by the azd command (optional)')
param azdEnvName string = ''

@description('Primary location for all resources')
param location string = resourceGroup().location
param azureMapsLocation string = 'eastus'

// See https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models
@description('OAI Region availability: East US, East US2, North Central US, South Central US, Sweden Central, West US, and West US3')
param openAI_deploy_location string = location

param openAI_model string = 'gpt-4.1'
param openAI_model_version string = '2025-04-14'
param openAI_api_version string = '2024-12-01-preview'

param openAI_agents_model string = 'gpt-4.1-mini'
param openAI_agents_model_version string = '2025-04-14'

// --------------------------------------------------------------------------------------------------------------
// Personal info
// --------------------------------------------------------------------------------------------------------------
@description('My IP address for network access')
param myIpAddress string = ''
@description('Id of the user executing the deployment')
param principalId string = ''

// --------------------------------------------------------------------------------------------------------------
// AI Hub Parameters
// --------------------------------------------------------------------------------------------------------------
@description('Friendly name for your Azure AI resource')
param aiProjectFriendlyName string = 'Agents Project resource'

@description('Description of your Azure AI resource displayed in AI studio')
param aiProjectDescription string = 'This is an example AI Project resource for use in Azure AI Studio.'

// --------------------------------------------------------------------------------------------------------------
// Existing images
// --------------------------------------------------------------------------------------------------------------
param chatImageName string = ''
param chatAppExists bool = false

// --------------------------------------------------------------------------------------------------------------
// Search Service
// --------------------------------------------------------------------------------------------------------------
// The free tier does not support managed identity (required) or semantic search (optional)
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2'])
param searchServiceSkuName string
param greenSoftwareSearchIndexName string
param computeDataSearchIndexName string
param searchSemanticConfiguration string
param searchServiceSemanticRankerLevel string
var actualSearchServiceSemanticRankerLevel = (searchServiceSkuName == 'free')
  ? 'disabled'
  : searchServiceSemanticRankerLevel
param searchIdentifierField string
param searchContentField string
param searchTitleField string
param searchEmbeddingField string
param searchUseVectorQuery bool

// Agents
var agentName = 'agent-for-workshop'

// --------------------------------------------------------------------------------------------------------------
// Other deployment switches
// --------------------------------------------------------------------------------------------------------------
@description('Should resources be created with public access?')
param publicAccessEnabled bool = true
@description('Add Role Assignments for the user assigned identity?')
param addRoleAssignments bool = true
@description('Should an Entra App Registration be created?')
param addAppRegistration bool = true
@description('Should a private link be created for the Search Service?')
param addPrivateLinkForSearch bool = true

// --------------------------------------------------------------------------------------------------------------
// -- Variables -------------------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
var resourceToken = toLower(uniqueString(resourceGroup().id, location))
var resourceGroupName = resourceGroup().name

var tags = { 'azd-env-name': azdEnvName }

var roleDefinitions = loadJsonContent('data/roleDefinitions.json')
// --------------------------------------------------------------------------------------------------------------
// -- Generate Resource Names -----------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module resourceNames 'resourcenames.bicep' = {
  name: 'resource-names'
  params: {
    applicationName: 'ai-workshop'
    resourceToken: resourceToken
  }
}
// --------------------------------------------------------------------------------------------------------------
// -- Entra App Registraion ----------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module appRegistration './entra/entra-resource-app.bicep' = if (addAppRegistration) {
  name: 'entra-app'
  params: {
    entraAppUniqueName: 'workshop-agent-client'
    entraAppDisplayName: 'Semantic Kernel Workshop Agent Client'
    tenantId: subscription().tenantId
    userAssignedIdentityPrincipleId: identity.outputs.managedIdentityPrincipalId
    OauthCallback: 'http://localhost:8501/oauth2callback'
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Container Registry ----------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module containerRegistry './core/host/containerregistry.bicep' = {
  name: 'containerregistry'
  params: {
    newRegistryName: resourceNames.outputs.ACR_Name
    location: location
    acrSku: publicAccessEnabled ? 'Basic' : 'Premium'
    tags: tags
    publicAccessEnabled: publicAccessEnabled
    myIpAddress: myIpAddress
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Log Analytics Workspace and App Insights ------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module logAnalytics './core/monitor/loganalytics.bicep' = {
  name: 'law'
  params: {
    newLogAnalyticsName: resourceNames.outputs.logAnalyticsWorkspaceName
    newApplicationInsightsName: resourceNames.outputs.appInsightsName
    location: location
    tags: tags
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Storage Resources ---------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  params: {
    name: resourceNames.outputs.storageAccountName
    location: location
    tags: tags
    publicNetworkAccess: publicAccessEnabled
    myIpAddress: myIpAddress
    containers: ['data', 'batch-input', 'batch-output', 'patterns-index-data', 'compute-index-data']
    resourcesWithAccess: [
      {
        resourceId: searchService.outputs.id
        tenantId: subscription().tenantId
      }
      {
        resourceId: openAI.outputs.id
        tenantId: subscription().tenantId
      }
    ]
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Key Vault Resources ---------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module identity './core/iam/identity.bicep' = {
  name: 'app-identity'
  params: {
    identityName: resourceNames.outputs.userAssignedIdentityName
    location: location
  }
}

module roleAssignments './core/iam/role-assignments.bicep' = if (addRoleAssignments) {
  name: 'identity-access'
  params: {
    registryName: containerRegistry.outputs.name
    storageAccountName: storage.outputs.name
    identityPrincipalId: identity.outputs.managedIdentityPrincipalId
    keyvaultName: keyVault.outputs.name
    openAiName: openAI.outputs.name
    aiSearchName: searchService.outputs.name
  }
}

module userRoleAssignments './core/iam/role-assignments.bicep' = if (addRoleAssignments && !empty(principalId)) {
  name: 'user-access'
  params: {
    registryName: containerRegistry.outputs.name
    storageAccountName: storage.outputs.name
    identityPrincipalId: principalId
    principalType: 'User'
    keyvaultName: keyVault.outputs.name
    openAiName: openAI.outputs.name
    aiSearchName: searchService.outputs.name
  }
}

module keyVault './core/security/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    commonTags: tags
    keyVaultName: substring('${resourceNames.outputs.keyVaultName}${resourceToken}', 0, 24)
    keyVaultOwnerUserId: principalId
    adminUserObjectIds: [
      {
        principalId: identity.outputs.managedIdentityPrincipalId
        principalType: 'ServicePrincipal'
      }
    ]
    publicNetworkAccess: publicAccessEnabled ? 'Enabled' : 'Disabled'
    keyVaultOwnerIpAddress: myIpAddress
    createUserAssignedIdentity: false
    useRBAC: true
    addRoleAssignments: addRoleAssignments
  }
}

var apiKeyValue = uniqueString(resourceGroup().id, location, 'api-key', resourceToken)
module apiKeySecret './core/security/keyvault-secret.bicep' = {
  name: 'secret-api-key'
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'api-key'
    secretValue: apiKeyValue
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Cognitive Services Resources ------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module searchService './core/search/search-services.bicep' = {
  name: 'search'
  params: {
    location: location
    name: resourceNames.outputs.searchServiceName
    publicNetworkAccess: publicAccessEnabled ? 'enabled' : 'disabled'
    myIpAddress: myIpAddress
    semanticSearch: actualSearchServiceSemanticRankerLevel
    managedIdentityId: identity.outputs.managedIdentityId
    sku: {
      name: searchServiceSkuName
    }
  }
}

module searchServicePrivateLink './core/search/search-privatelink.bicep' = if(addPrivateLinkForSearch) {
  name: 'search-privatelink'
  params: {
    searchName: searchService.outputs.name
    openAiServiceName: openAI.outputs.name
    storageAccountName: storage.outputs.name
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Azure OpenAI Resources ------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module openAI './core/ai/cognitive-services.bicep' = {
  name: 'openai'
  params: {
    managedIdentityId: identity.outputs.managedIdentityId
    name: resourceNames.outputs.cogServiceName
    location: !empty(openAI_deploy_location) ? openAI_deploy_location : location // this may be different than the other resources
    kind: 'AIServices'
    tags: tags
    appInsightsName: logAnalytics.outputs.applicationInsightsName
    textEmbeddings: [
      {
        name: 'text-embedding'
        model: {
          format: 'OpenAI'
          name: 'text-embedding-ada-002'
          version: '2'
        }
        sku: {
          name: 'Standard'
          capacity: 30
        }
      }
      {
        name: 'text-embedding-large'
        model: {
          format: 'OpenAI'
          name: 'text-embedding-3-large'
          version: '1'
        }
        sku: {
          name: 'Standard'
          capacity: 30
        }
      }
    ]
    chatGpt_Standard: {
      DeploymentName: openAI_agents_model
      ModelName: openAI_agents_model
      ModelVersion: openAI_agents_model_version
      sku: {
        name: 'GlobalStandard'
        capacity: 320
      }
    }
    chatGpt_Premium: {
      DeploymentName: openAI_model
      ModelName: openAI_model
      ModelVersion: openAI_model_version
      sku: {
        name: 'GlobalStandard'
        capacity: 100
      }
    }
    publicNetworkAccess: publicAccessEnabled ? 'Enabled' : 'Disabled'
    myIpAddress: myIpAddress
  }
  dependsOn: [
    searchService
  ]
}

module aiProject 'core/ai/ai-project.bicep' = {
  name: 'aiProject'
  params: {
    // workspace organization
    account_name: openAI.outputs.name
    project_name: resourceNames.outputs.aiHubProjectName
    display_name: aiProjectFriendlyName
    description: aiProjectDescription
    managedIdentityId: identity.outputs.managedIdentityId
    location: location
    tags: tags
  }
}

module bing 'bing/connection-bing-grounding.bicep' = {
  name: 'bing-grounding'
  params: {
    aiFoundryName: openAI.outputs.name
    tags: tags
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Maps for weather -------- ---------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module maps 'maps/maps.bicep' = {
  name: 'maps'
  params: {
    location: azureMapsLocation
    name: resourceNames.outputs.maps
    tags: tags
    storageAccountName: storage.outputs.name
    roleAssignments: addRoleAssignments
      ? [
          {
            principalId: identity.outputs.managedIdentityPrincipalId
            roleDefinitionId: roleDefinitions.maps.AzureMapsDataReader
          }
          {
            principalId: principalId
            roleDefinitionId: roleDefinitions.maps.AzureMapsDataReader
            principalType: 'User'
          }
        ]
      : []
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Container App Environment ---------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
module managedEnvironment './core/host/managedEnvironment.bicep' = {
  name: 'caenv'
  params: {
    newEnvironmentName: resourceNames.outputs.caManagedEnvName
    location: location
    logAnalyticsWorkspaceName: logAnalytics.outputs.logAnalyticsWorkspaceName
    logAnalyticsRgName: resourceGroupName
    tags: tags
    publicAccessEnabled: publicAccessEnabled
  }
}

module simple_chat './core/host/container-app-upsert.bicep' = {
  name: 'simple-chat'
  params: {
    tags: union(tags, { 'azd-service-name': 'simple-chat' })
    appName: resourceNames.outputs.containerChatName
    location: location
    targetPort: 8501
    myIpAddress: myIpAddress
    exists: chatAppExists
    imageName: chatImageName
    managedEnvironmentName: managedEnvironment.outputs.name
    managedEnvironmentRg: managedEnvironment.outputs.resourceGroupName
    containerRegistryName: containerRegistry.outputs.name
    userAssignedIdentityName: identity.outputs.managedIdentityName
    env: [
      { name: 'AZURE_OPENAI_ENDPOINT', value: openAI.outputs.endpoint }
      { name: 'AZURE_OPENAI_DEPLOYMENT', value: openAI_model }
      { name: 'AZURE_OPENAI_API_VERSION', value: openAI_api_version }
      { name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', value: openAI_model }
      { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT', value: openAI.outputs.textEmbeddings[1].name }
      { name: 'AZURE_PATTERNS_SEARCH_INDEX', value: greenSoftwareSearchIndexName }
      { name: 'AZURE_COMPUTE_SEARCH_INDEX', value: computeDataSearchIndexName }
      { name: 'AZURE_SEARCH_ENDPOINT', value: searchService.outputs.endpoint }
      {
        name: 'AZURE_AI_FOUNDRY_CONNECTION_STRING'
        value: empty(aiProject) ? '' : aiProject.outputs.projectConnectionString
      }
      { name: 'AZURE_AI_PROJECT_RESEARCH_AGENT_NAME', value: agentName }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: logAnalytics.outputs.appInsightsConnectionString }
      { name: 'AZURE_CLIENT_ID', value: identity.outputs.managedIdentityClientId }
      { name: 'AZURE_SDK_TRACING_IMPLEMENTATION', value: 'opentelemetry' }
      { name: 'AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED', value: 'true' }
      { name: 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS', value: 'true' }
      { name: 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE', value: 'true' }
      { name: 'APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL', value: 'true' }
      { name: 'APPLICATIONINSIGHTS_METRIC_NAMESPACE_OPT_IN', value: 'false' }
      { name: 'AZURE_MAPS_CLIENT_ID', value: maps.outputs.clientId }
    ]
    secrets: {}
  }
}

// --------------------------------------------------------------------------------------------------------------
// -- Outputs ---------------------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------------------------
output SUBSCRIPTION_ID string = subscription().subscriptionId
output AZURE_TENANT_ID string = tenant().tenantId

output USER_ASSIGNED_IDENTITY_ID string = identity.outputs.managedIdentityId
output ACR_NAME string = containerRegistry.outputs.name
output ACR_URL string = containerRegistry.outputs.loginServer
output AI_ENDPOINT string = openAI.outputs.endpoint
output AI_ID string = openAI.outputs.id
output AI_PROJECT_NAME string = resourceNames.outputs.aiHubProjectName
output AI_SEARCH_ENDPOINT string = searchService.outputs.endpoint
// output API_CONTAINER_APP_FQDN string = containerAppAPI.outputs.fqdn
// output API_CONTAINER_APP_NAME string = containerAppAPI.outputs.name
output AZURE_CONTAINER_ENVIRONMENT_NAME string = managedEnvironment.outputs.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output AZURE_RESOURCE_GROUP string = resourceGroupName
output MANAGED_ENVIRONMENT_ID string = managedEnvironment.outputs.id
output MANAGED_ENVIRONMENT_NAME string = managedEnvironment.outputs.name
output RESOURCE_TOKEN string = resourceToken
output STORAGE_ACCOUNT_BATCH_IN_CONTAINER string = storage.outputs.containerNames[1].name
output STORAGE_ACCOUNT_BATCH_OUT_CONTAINER string = storage.outputs.containerNames[2].name
output STORAGE_ACCOUNT_CONTAINER string = storage.outputs.containerNames[0].name
output STORAGE_ACCOUNT_NAME string = storage.outputs.name
output KEY_VAULT_NAME string = keyVault.outputs.name

// new for indexing
output AZURE_PATTERNS_SEARCH_INDEX string = greenSoftwareSearchIndexName
output AZURE_COMPUTE_SEARCH_INDEX string = computeDataSearchIndexName
output AZURE_SEARCH_SEMANTIC_CONFIGURATION string = searchSemanticConfiguration
output AZURE_SEARCH_IDENTIFIER_FIELD string = searchIdentifierField
output AZURE_SEARCH_CONTENT_FIELD string = searchContentField
output AZURE_SEARCH_TITLE_FIELD string = searchTitleField
output AZURE_SEARCH_EMBEDDING_FIELD string = searchEmbeddingField
output AZURE_SEARCH_USE_VECTOR_QUERY bool = searchUseVectorQuery

output AZURE_OPENAI_ENDPOINT string = openAI.outputs.endpoint
output AZURE_OPENAI_ENDPOINT_FOR_INDEXING string = 'https://${openAI.outputs.name}.openai.azure.com/'
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT string = openAI.outputs.textEmbeddings[1].name
output AZURE_OPENAI_EMBEDDING_MODEL string = openAI.outputs.textEmbeddings[1].model.name
output AZURE_OPENAI_MODEL string = openAI_model
output AZURE_OPENAI_AGENTS_MODEL string = openAI_agents_model
output AZURE_OPENAI_API_VERSION string = openAI_api_version
output AZURE_SEARCH_ENDPOINT string = searchService.outputs.endpoint
output AZURE_STORAGE_ENDPOINT string = 'https://${storage.outputs.name}.blob.${environment().suffixes.storage}'
output AZURE_STORAGE_CONNECTION_STRING string = 'ResourceId=${storage.outputs.id}'
output AZURE_PATTERNS_INDEX_STORAGE_CONTAINER string = storage.outputs.containerNames[3].name
output AZURE_COMPUTE_INDEX_STORAGE_CONTAINER string = storage.outputs.containerNames[4].name
output AZURE_STORAGE_ID string = storage.outputs.id

output AZURE_AI_FOUNDRY_CONNECTION_STRING string = empty(aiProject) ? '' : aiProject.outputs.projectConnectionString

output AZURE_AI_PROJECT_RESEARCH_AGENT_NAME string = agentName

output APPLICATIONINSIGHTS_CONNECTION_STRING string = logAnalytics.outputs.appInsightsConnectionString

output AZURE_MAPS_CLIENT_ID string = maps.outputs.clientId

// App registration outputs
output ENTRA_APP_ID string = addAppRegistration ? appRegistration.outputs.entraAppId : ''

output BING_CONNECTION_NAME string = bing.outputs.BING_CONNECTION_NAME
output BING_CONNECTION_ID string = bing.outputs.BING_CONNECTION_ID
