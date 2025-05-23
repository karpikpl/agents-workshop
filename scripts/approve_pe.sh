#!/bin/bash
# filepath: /home/pkarpala/projects/philips/EmissionsCopilot/scripts/approve_all_pl_connections.sh

# Set these variables as needed:
AZURE_STORAGE_ID=$(azd env get-value AZURE_STORAGE_ID)
AI_ID=$(azd env get-value AI_ID)

approvalMessage="Approved automatically via script"

# List all private endpoint connections with 'Pending' status on the resource
pendingConnections=$(az network private-endpoint-connection list \
  --id "$AZURE_STORAGE_ID" \
  --query "[?properties.privateLinkServiceConnectionState.status=='Pending'].id" -o tsv)

echo "Found pending storage private endpoint connections:"
echo "$pendingConnections"

# Loop over each connection and approve it
for connectionId in $pendingConnections; do
  echo "Approving connection: $connectionId"
  az network private-endpoint-connection approve \
    --id "$connectionId" \
    --description "$approvalMessage"
done

pendingConnections=$(az network private-endpoint-connection list \
  --id "$AI_ID" \
  --query "[?properties.privateLinkServiceConnectionState.status=='Pending'].id" -o tsv)

echo "Found pending OpenAI private endpoint connections:"
echo "$pendingConnections"

# Loop over each connection and approve it
for connectionId in $pendingConnections; do
  echo "Approving connection: $connectionId"
  az network private-endpoint-connection approve \
    --id "$connectionId" \
    --description "$approvalMessage"
done