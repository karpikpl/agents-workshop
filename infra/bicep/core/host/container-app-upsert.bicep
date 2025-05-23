metadata description = 'Creates or updates an existing Azure Container App.'
param appName string
param location string = resourceGroup().location
param tags object = {}

@description('The environment name for the container apps')
param managedEnvironmentName string
param managedEnvironmentRg string

@description('The number of CPU cores allocated to a single container instance, e.g., 0.5')
param containerCpuCoreCount string = '0.5'

@description('The maximum number of replicas to run. Must be at least 1.')
@minValue(1)
param containerMaxReplicas int = 10

@description('The amount of memory allocated to a single container instance, e.g., 1Gi')
param containerMemory string = '1.0Gi'

@description('The minimum number of replicas to run. Must be at least 1.')
@minValue(1)
param containerMinReplicas int = 1

@description('The name of the container')
param containerName string = 'main'

@description('The name of the container registry')
param containerRegistryName string = ''

@description('Hostname suffix for container registry. Set when deploying to sovereign clouds')
param containerRegistryHostSuffix string = 'azurecr.io'

@allowed([ 'http', 'grpc' ])
@description('The protocol used by Dapr to connect to the app, e.g., HTTP or gRPC')
param daprAppProtocol string = 'http'

@description('Enable or disable Dapr for the container app')
param daprEnabled bool = false

@description('The Dapr app ID')
param daprAppId string = containerName

@description('Specifies if the resource already exists')
param exists bool = false

@description('Specifies if Ingress is enabled for the container app')
param ingressEnabled bool = true

@description('The name of the container image')
param imageName string = ''

@description('The secrets required for the container')
@secure()
param secrets object = {}

@description('The environment variables for the container')
param env array = []

@description('Specifies if the resource ingress is exposed externally')
param external bool = true

@description('The target port for the container')
param targetPort int = 80

@description('Ip Address to allow access')
param myIpAddress string = ''

@description('The name of the user-assigned identity')
param userAssignedIdentityName string

@description('Set to true to disable health probes')
param disableHealthProbes bool = false

resource existingApp 'Microsoft.App/containerApps@2023-05-02-preview' existing = if (exists) {
  name: appName
}

module app 'container-app.bicep' = {
  name: '${deployment().name}-update'
  params: {
    appName: appName
    location: location
    tags: tags
    ingressEnabled: ingressEnabled
    myIpAddress: myIpAddress
    containerName: containerName
    managedEnvironmentName: managedEnvironmentName
    managedEnvironmentRg: managedEnvironmentRg
    containerRegistryName: containerRegistryName
    containerRegistryHostSuffix: containerRegistryHostSuffix
    containerCpuCoreCount: containerCpuCoreCount
    containerMemory: containerMemory
    containerMinReplicas: containerMinReplicas
    containerMaxReplicas: containerMaxReplicas
    daprEnabled: daprEnabled
    daprAppId: daprAppId
    daprAppProtocol: daprAppProtocol
    secrets: secrets
    external: external
    env: env
    imageName: !empty(imageName) ? imageName : exists ? existingApp.properties.template.containers[0].image : ''
    targetPort: targetPort
    userAssignedIdentityName: userAssignedIdentityName
    disableHealthProbes: disableHealthProbes
  }
}

// --------------------------------------------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------------------------------------------
output id string = app.outputs.id
output name string = app.outputs.name
output fqdn string = app.outputs.fqdn
output imageName string = app.outputs.imageName
output uri string = app.outputs.uri
