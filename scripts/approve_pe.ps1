# Approve all pending private endpoint connections for Storage and OpenAI resources

# Get environment variables using azd
$AZURE_STORAGE_ID = azd env get-value AZURE_STORAGE_ID
$AI_ID = azd env get-value AI_ID

$approvalMessage = "Approved automatically via script"

# Approve pending Storage private endpoint connections
$pendingConnections = az network private-endpoint-connection list `
    --id $AZURE_STORAGE_ID `
    --query "[?properties.privateLinkServiceConnectionState.status=='Pending'].id" -o tsv

Write-Host "Found pending storage private endpoint connections:"
Write-Host $pendingConnections

foreach ($connectionId in $pendingConnections) {
    Write-Host "Approving connection: $connectionId"
    az network private-endpoint-connection approve `
        --id $connectionId `
        --description $approvalMessage
}

# Approve pending OpenAI private endpoint connections
$pendingConnections = az network private-endpoint-connection list `
    --id $AI_ID `
    --query "[?properties.privateLinkServiceConnectionState.status=='Pending'].id" -o tsv

Write-Host "Found pending OpenAI private endpoint connections:"
Write-Host $pendingConnections

foreach ($connectionId in $pendingConnections) {
    Write-Host "Approving connection: $connectionId"
    az network private-endpoint-connection approve `
        --id $connectionId `
        --description $approvalMessage
}