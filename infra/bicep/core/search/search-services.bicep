param name string = ''
param location string = resourceGroup().location
param tags object = {}

param existingSearchServiceName string = ''

param sku object = {
  name: 'standard'
  //name: 'basic'
}

@description('Ip Address to allow access to the Azure Search Service')
param myIpAddress string = ''
param partitionCount int = 1
@allowed([
  'enabled'
  'disabled'
])
param publicNetworkAccess string = 'disabled'
param replicaCount int = 1

@description('Optional. Sets options that control the availability of semantic search. This configuration is only possible for certain search SKUs in certain locations.')
param semanticSearch string?

param privateEndpointSubnetId string = ''
param privateEndpointName string = ''
param managedIdentityId string = ''

// --------------------------------------------------------------------------------------------------------------
// Variables
// --------------------------------------------------------------------------------------------------------------
var useExistingSearchService = !empty(existingSearchServiceName)
var resourceGroupName = resourceGroup().name
var searchKeySecretName = 'search-key'

// --------------------------------------------------------------------------------------------------------------
resource existingSearchService 'Microsoft.Search/searchServices@2024-06-01-preview' existing = if (useExistingSearchService) {
  name: existingSearchServiceName
}

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = if (!useExistingSearchService) {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    networkRuleSet: {
      bypass: 'AzurePortal'
      ipRules: empty(myIpAddress) || publicNetworkAccess == 'enabled'
        ? []
        : [
            {
              value: myIpAddress
            }
          ]
    }
    partitionCount: partitionCount
    publicNetworkAccess: publicNetworkAccess
    replicaCount: replicaCount
    semanticSearch: semanticSearch
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
  sku: sku
}

module privateEndpoint '../networking/private-endpoint.bicep' = if (!useExistingSearchService && !empty(privateEndpointSubnetId)) {
  name: '${name}-private-endpoint'
  params: {
    tags: tags
    location: location
    privateEndpointName: privateEndpointName
    groupIds: ['searchService']
    targetResourceId: search.id
    subnetId: privateEndpointSubnetId
  }
}

// --------------------------------------------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------------------------------------------
output id string = useExistingSearchService ? existingSearchService.id : search.id
output name string = useExistingSearchService ? existingSearchService.name : search.name
output endpoint string = useExistingSearchService
  ? 'https://${existingSearchServiceName}.search.windows.net/'
  : 'https://${name}.search.windows.net/'
output resourceGroupName string = resourceGroupName
output searchKeySecretName string = searchKeySecretName
output keyVaultSecretName string = searchKeySecretName
output privateEndpointId string = empty(privateEndpointSubnetId) ? '' : privateEndpoint.outputs.privateEndpointId
output privateEndpointName string = privateEndpointName
