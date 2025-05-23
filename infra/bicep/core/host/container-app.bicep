metadata description = 'Creates a container app in an Azure Container App environment.'
@maxLength(32)
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
param containerName string = 'app'

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

@description('Specifies if Ingress is enabled for the container app')
param ingressEnabled bool = true

@description('Allowed origins')
param allowedOrigins array = []

@description('Specifies if the resource ingress is exposed externally')
param external bool = true
param imageName string = ''

@description('The name of the user-assigned identity')
param userAssignedIdentityName string

@description('The target port for the container')
param targetPort int = 80

@description('Ip Address to allow access')
param myIpAddress string = ''

@description('Set to true to disable health probes')
param disableHealthProbes bool = false

@description('The secrets required for the container, with the key being the secret name and the value being the key vault URL')
@secure()
param secrets object = {}

@description('The environment variables for the container')
param env array = []

// --------------------------------------------------------------------------------------------------------------
resource containerAppEnvironmentResource 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: managedEnvironmentName
  scope: resourceGroup(managedEnvironmentRg)
}

resource userIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: userAssignedIdentityName
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
  // It is critical that the identity is granted ACR pull access before the app is created
  // otherwise the container app will throw a provision error
  // This also forces us to use an user assigned managed identity since there would no way to 
  // provide the system assigned identity with the ACR pull access before the app is created
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userIdentity.id}': {}
    }
  }
  
  properties: {
    environmentId: containerAppEnvironmentResource.id
    configuration: {
      ingress: ingressEnabled ? {
        external: external
        targetPort: targetPort
        transport: 'auto'
        corsPolicy: {
          allowedOrigins: union([ 'https://portal.azure.com', 'https://ms.portal.azure.com' ], allowedOrigins)
        }
        ipSecurityRestrictions: empty(myIpAddress) ? [] : [
          {
            name: 'AllowMyIp'
            action: 'Allow'
            ipAddressRange: myIpAddress
            description: 'Allow access from my IP address'
          }
        ]
      } : null
      dapr: daprEnabled ? {
        enabled: true
        appId: daprAppId
        appProtocol: daprAppProtocol
        appPort: ingressEnabled ? targetPort : 0
      } : { enabled: false }
      secrets: [for secret in items(secrets): {
        name: secret.key
        identity: userIdentity.id
        keyVaultUrl: secret.value
      }]
      registries: [
        {
          identity: userIdentity.id
          server: '${containerRegistryName}.${containerRegistryHostSuffix}'
        }
      ]
    }
    template: {
      scale: {
        minReplicas: containerMinReplicas
        maxReplicas: containerMaxReplicas
      }
      containers: [
        {
          name: containerName
          image: !empty(imageName) ? imageName : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
              cpu: json(containerCpuCoreCount)
              memory: containerMemory
          }
          env: env
          probes: disableHealthProbes ? [] : [
            {
              type: 'startup'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 3
              periodSeconds: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/ready'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 3
              periodSeconds: 10
            }
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 7
              periodSeconds: 60
            }
          ]
        }
      ]
    }
  }
}

// --------------------------------------------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------------------------------------------
output id string = containerApp.id
output name string = containerApp.name
output fqdn string = containerApp.properties.configuration.ingress.fqdn
output imageName string = imageName
output uri string = ingressEnabled ? 'https://${containerApp.properties.configuration.ingress.fqdn}' : ''
