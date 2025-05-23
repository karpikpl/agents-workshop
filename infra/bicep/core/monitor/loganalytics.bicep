param newLogAnalyticsName string = ''
param newApplicationInsightsName string = ''

param existingLogAnalyticsName string = ''
param existingLogAnalyticsRgName string = ''
param existingApplicationInsightsName string = ''
param existingAzureMonitorPrivateLinkScopeName string = ''

param location string = resourceGroup().location
param tags object = {}
param azureMonitorPrivateLinkScopeName string = ''
param azureMonitorPrivateLinkScopeResourceGroupName string = ''
param privateEndpointSubnetId string = ''
param privateEndpointName string = ''
param publicNetworkAccessForIngestion string = 'Enabled'
param publicNetworkAccessForQuery string = 'Enabled'

var useExistingLogAnalytics = !empty(existingLogAnalyticsName)
var useExistingAppInsights = !empty(existingApplicationInsightsName)
var useExistingAzureMonitorPrivateLinkScope = !empty(existingAzureMonitorPrivateLinkScopeName)

resource existingLogAnalyticsResource 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = if (useExistingLogAnalytics) {
  name: existingLogAnalyticsName
  scope: resourceGroup(existingLogAnalyticsRgName)
}

resource newLogAnalyticsResource 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (!useExistingLogAnalytics){
  name: newLogAnalyticsName
  location: location
  tags: tags
  properties: any({
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
    publicNetworkAccessForIngestion: publicNetworkAccessForIngestion
    publicNetworkAccessForQuery: publicNetworkAccessForQuery
  })
}

resource existingApplicationInsightsResource 'Microsoft.Insights/components@2020-02-02' existing = if (useExistingAppInsights) {
  name: existingApplicationInsightsName
}
resource newApplicationInsightsResource 'Microsoft.Insights/components@2020-02-02' = if (!useExistingAppInsights) {
  name: newApplicationInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: newLogAnalyticsResource.id
    publicNetworkAccessForIngestion: publicNetworkAccessForIngestion
    publicNetworkAccessForQuery: publicNetworkAccessForQuery
  }
}

resource azureMonitorPrivateLinkScope 'Microsoft.Insights/privateLinkScopes@2021-07-01-preview' existing = if (!empty(existingAzureMonitorPrivateLinkScopeName)) {
  name: existingAzureMonitorPrivateLinkScopeName
  scope: resourceGroup(azureMonitorPrivateLinkScopeResourceGroupName)
}

resource azureMonitorPrivateLinkScopeNew 'Microsoft.Insights/privateLinkScopes@2021-07-01-preview' = if (!empty(azureMonitorPrivateLinkScopeName)) {
  name: azureMonitorPrivateLinkScopeName
  location: 'global'
  tags: tags
  properties: {
    accessModeSettings: {
      ingestionAccessMode: publicNetworkAccessForIngestion == 'Enabled' ? 'Open' : 'PrivateOnly'
      queryAccessMode: publicNetworkAccessForQuery == 'Enabled' ? 'Open' : 'PrivateOnly'
    }
  }

  resource lawScopedResource 'scopedResources@2021-07-01-preview' = {
    name: 'law-link'
    properties: {
      linkedResourceId: useExistingLogAnalytics ? existingLogAnalyticsResource.id : newLogAnalyticsResource.id
    }
  }
  resource appInScopedResource 'scopedResources@2021-07-01-preview' = {
    name: 'appIn-link'
    properties: {
      linkedResourceId: useExistingAppInsights ? existingApplicationInsightsResource.id : newApplicationInsightsResource.id
    }
  }
}


module azureMonitorPrivateLinkScopePrivateEndpoint '../networking/private-endpoint.bicep' = if (!empty(privateEndpointSubnetId)) {
  name: 'azure-monitor-private-link-scope-private-endpoint'
  params: {
    privateEndpointName: privateEndpointName
    groupIds: ['azuremonitor']
    targetResourceId: useExistingAzureMonitorPrivateLinkScope ? azureMonitorPrivateLinkScope.id : azureMonitorPrivateLinkScopeNew.id
    subnetId: privateEndpointSubnetId
  }
}

output applicationInsightsId string = useExistingAppInsights ? existingApplicationInsightsResource.id : newApplicationInsightsResource.id
output applicationInsightsName string = useExistingAppInsights ? existingApplicationInsightsResource.name : newApplicationInsightsResource.name
output logAnalyticsWorkspaceId string = useExistingLogAnalytics ? existingLogAnalyticsResource.id : newLogAnalyticsResource.id
output logAnalyticsWorkspaceName string = useExistingLogAnalytics ? existingLogAnalyticsResource.name : newLogAnalyticsResource.name
output appInsightsConnectionString string = useExistingAppInsights ? existingApplicationInsightsResource.properties.ConnectionString : newApplicationInsightsResource.properties.ConnectionString
output privateEndpointName string = privateEndpointName
output privateLinkScopeId string = useExistingAzureMonitorPrivateLinkScope ? azureMonitorPrivateLinkScope.id : azureMonitorPrivateLinkScopeNew.id
