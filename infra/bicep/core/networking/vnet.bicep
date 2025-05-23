param location string = resourceGroup().location
param modelLocation string = location

param existingVirtualNetworkName string = ''
param newVirtualNetworkName string = ''
param vnetAddressPrefix string

@description('Ip Address to allow access to the Azure Search Service')
param myIpAddress string = ''

param subnet1Name string
param subnet2Name string
param subnet1Prefix string
param subnet2Prefix string
param otherSubnets object[] = []

var useExistingResource = !empty(existingVirtualNetworkName)

resource existingVirtualNetwork 'Microsoft.Network/virtualNetworks@2024-01-01' existing = if (useExistingResource) {
  name: existingVirtualNetworkName
  resource subnet1 'subnets' existing = {
    name: subnet1Name
  }
  resource subnet2 'subnets' existing = {
    name: subnet2Name
  }
}

// Create an NSG
resource nsg 'Microsoft.Network/networkSecurityGroups@2022-09-01' = if (empty(existingVirtualNetworkName)) {
  name: 'nsg-allow-my-ip'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowMyIP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourceAddressPrefix: myIpAddress
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
    ]
  }
}

var moreSubnets = [
  for subnet in otherSubnets: {
    name: subnet.name
    properties: union(
      subnet.properties,
      !useExistingResource
        ? {
            networkSecurityGroup: {
              id: nsg.id
            }
          }
        : {}
    )
  }
]

resource newVirtualNetwork 'Microsoft.Network/virtualNetworks@2024-01-01' = if (!useExistingResource) {
  name: newVirtualNetworkName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: union(
      [
        {
          name: subnet1Name
          properties: {
            addressPrefix: subnet1Prefix
            networkSecurityGroup: {
              id: nsg.id
            }
            serviceEndpoints: [
              {
                service: 'Microsoft.KeyVault'
                locations: [
                  location
                ]
              }
              {
                service: 'Microsoft.Storage'
                locations: [
                  location
                ]
              }
              {
                service: 'Microsoft.CognitiveServices'
                locations: [
                  modelLocation
                ]
              }
            ]
          }
        }
        {
          name: subnet2Name
          properties: {
            addressPrefix: subnet2Prefix
            networkSecurityGroup: {
              id: nsg.id
            }
            delegations: [
              {
                name: 'Microsoft.app/environments'
                properties: {
                  serviceName: 'Microsoft.app/environments'
                }
              }
            ]
          }
        }
      ],
      moreSubnets
    )
  }

  resource subnet1 'subnets' existing = {
    name: subnet1Name
  }

  resource subnet2 'subnets' existing = {
    name: subnet2Name
  }
}

output vnetResourceId string = useExistingResource ? existingVirtualNetwork.id : newVirtualNetwork.id
output vnetName string = useExistingResource ? existingVirtualNetwork.name : newVirtualNetwork.name
output vnetAddressPrefix string = useExistingResource
  ? existingVirtualNetwork.properties.addressSpace.addressPrefixes[0]
  : newVirtualNetwork.properties.addressSpace.addressPrefixes[0]
output subnet1ResourceId string = useExistingResource
  ? existingVirtualNetwork::subnet1.id
  : newVirtualNetwork::subnet1.id
output subnet2ResourceId string = useExistingResource
  ? existingVirtualNetwork::subnet2.id
  : newVirtualNetwork::subnet2.id
output allSubnets array = useExistingResource
  ? existingVirtualNetwork.properties.subnets
  : newVirtualNetwork.properties.subnets
