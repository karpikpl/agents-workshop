param tags object = {}
param vnetResourceId string
param zoneName string = ''
param zoneNames string[] = []
param privateEndpointNames string[] = []
param existingZonesIds string[] = []

var allZoneNames = union(zoneNames, empty(zoneName) ? [] : [zoneName]) 

module zones 'private-dns.bicep' = [
  for (zoneName, i) in allZoneNames: {
    name: '${zoneName}-zone'
    params: {
      zoneName: zoneName
      vnetResourceId: vnetResourceId
      tags: tags
    }
  }
]

resource pe 'Microsoft.Network/privateEndpoints@2023-06-01' existing = [
  for privateEndpointName in privateEndpointNames: {
    name: privateEndpointName
  }
]

var existingZoneConfigs = [for zoneId in existingZonesIds: {
  name: 'config for ${zoneId}'
  properties: {
    privateDnsZoneId: zoneId
  }
}]

var newZoneConfigs = [for (zoneName, index) in allZoneNames: {
  name: 'config for ${zoneName}'
  properties: {
    privateDnsZoneId: resourceId('Microsoft.Network/privateDnsZones', zoneName)
  }
}]

resource privateEndpointDnsGroupname 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-07-01' = [
  for (privateEndpointName, i) in privateEndpointNames: {
    parent: pe[i]
    dependsOn: zones
    name: '${privateEndpointName}-dnsgroup'
    properties: {
      privateDnsZoneConfigs: union(existingZoneConfigs, newZoneConfigs)
    }
  }
]

output ids string[] = [for item in newZoneConfigs: item.properties.privateDnsZoneId]
