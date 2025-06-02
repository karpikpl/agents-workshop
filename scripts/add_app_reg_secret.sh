#!/bin/bash

set -e

echo "Loading azd .env file from current environment"

# Use the `get-values` azd command to retrieve environment variables from the `.env` file
APP_ID=$(azd env get-value ENTRA_APP_ID)
SECRET_NAME="agents-workshop-secret"

# Skip if ENTRA_APP_ID is empty
if [[ -z "$APP_ID" ]]; then
    echo "ENTRA_APP_ID is empty. Skipping secret creation."
    exit 0
fi

# do nothing if the secret already exists
EXISTING_SECRET=$(azd env get-value ENTRA_APP_SECRET)
if [[ -n "$EXISTING_SECRET" ]]; then
    echo "Secret '$SECRET_NAME' already exists for app '$APP_ID'. Skipping creation."
    exit 0
fi

SECRET_VALUE=$(az ad app credential reset \
  --id "$APP_ID" \
  --display-name "$SECRET_NAME" \
  --years 1 \
  --query "password" \
  -o tsv)

azd env set ENTRA_APP_SECRET "$SECRET_VALUE"