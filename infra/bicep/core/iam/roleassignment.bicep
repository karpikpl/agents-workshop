param resourceId string
param roleDefinitionId string
param principalId string
param registryName string

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceId, registryName, 'AcrPullTestUserAssigned')
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: roleDefinitionId
  }
}

output resourceId string = resourceId
output roleAssignmentId string = roleAssignment.id
