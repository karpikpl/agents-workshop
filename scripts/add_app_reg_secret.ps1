# Requires: Azure CLI and azd installed and logged in

Write-Host "Loading azd .env file from current environment"

# Get ENTRA_APP_ID from azd environment
$APP_ID = azd env get-value ENTRA_APP_ID
$SECRET_NAME = "agents-workshop-secret"

# Skip if ENTRA_APP_ID is empty
if ([string]::IsNullOrWhiteSpace($APP_ID)) {
    Write-Host "ENTRA_APP_ID is empty. Skipping secret creation."
    exit 0
}

# Check if secret already exists
$EXISTING_SECRET = azd env get-value ENTRA_APP_SECRET
if (-not [string]::IsNullOrWhiteSpace($EXISTING_SECRET)) {
    Write-Host "Secret '$SECRET_NAME' already exists for app '$APP_ID'. Skipping creation."
    exit 0
}

# Create new secret
$SECRET_VALUE = az ad app credential reset `
    --id $APP_ID `
    --display-name $SECRET_NAME `
    --years 1 `
    --query "password" `
    -o tsv

azd env set ENTRA_APP_SECRET $SECRET_VALUE