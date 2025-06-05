# Azure AI Agent Service with MSAL Authentication

A Gradio-based web application that provides an enterprise chat interface powered by Azure AI services, with automatic authentication and secure Azure Entra ID integration using MSAL.

## Features

- 🔐 **Automatic Authentication**: Seamless Azure Entra ID login with auto-redirect
- 🚀 **Protected Routes**: All sensitive endpoints require authentication
- 🤖 **AI-Powered Chat**: Azure AI Agent Service with multiple tools
- 🔍 **Web Search**: Bing search integration for real-time information
- 📁 **File Processing**: Upload and analyze documents
- 🌤️ **Weather API**: Real-time weather information
- 📈 **Stock Data**: Financial information retrieval
- ✉️ **Email Integration**: Send emails through the agent

## Authentication Flow

The application implements automatic authentication with the following behavior:

1. **Unauthenticated Access**: 
   - Visiting `/` automatically redirects to `/login`
   - Protected routes require authentication

2. **Authentication Process**:
   - `/login` redirects to Azure Entra ID
   - After successful authentication, users are redirected to `/`
   - Session is maintained across requests

3. **API Endpoints**:
   - `/auth/status` - Check authentication status (API-friendly)
   - `/health` - Health check (no authentication required)
   - `/ready` - Readiness check (no authentication required)

## Prerequisites

1. **Azure Subscription** with the following services:
   - Azure AI Foundry (or Azure OpenAI)
   - Azure Entra ID (for authentication)
   - Bing Search API (optional)

2. **Python 3.13+** installed

3. **App Registration** in Azure Entra ID

## Setup Instructions

### 1. Azure Entra ID App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Entra ID** > **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: `Azure AI Agent Service`
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: `http://localhost:8501/auth/callback` (for development)
5. After creation, note down:
   - **Application (client) ID**
   - **Directory (tenant) ID**
6. Go to **Certificates & secrets** > **Client secrets**
7. Create a new client secret and note the **Value**

### 2. API Permissions

In your App Registration:
1. Go to **API permissions**
2. Add the following permissions:
   - **Microsoft Graph**: `openid`, `profile`, `email`
   - **Azure Service Management**: `user_impersonation`
   - **Cognitive Services**: `user_impersonation`

### 3. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` using the example

### 4. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 5. Run the Application

Using the startup script (recommended):
```bash
./start.sh
```

Or manually:
```bash
uvicorn main:app --host 0.0.0.0 --port 8501 --reload
```


## Authentication Flow

1. **User visits** `http://localhost:8000/`
2. **If not authenticated**, they see login information
3. **Click login** redirects to Azure Entra ID
4. **After authentication**, user is redirected back to the app
5. **Access the chat interface** at `http://localhost:8000`

## API Endpoints

- `GET /login` - Initiate Azure AD login
- `GET /auth/callback` - Handle Azure AD callback
- `GET /logout` - Logout and clear session
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check
- `/` - Main chat interface (requires authentication)

## Token Management

The application automatically handles:
- ✅ **Token refresh** when access tokens expire
- ✅ **Session management** with secure storage
- ✅ **Token validation** for each request
- ✅ **Automatic re-authentication** when refresh fails

## Security Features

- **State parameter** validation for OAuth flows
- **Secure session** storage with encryption
- **Token expiration** handling with automatic refresh
- **Proper logout** that clears both local and Azure sessions
- **CORS protection** and request validation

## Troubleshooting

### Common Issues

1. **"Authentication required" error**
   - Check your AAD configuration in `.env`
   - Verify the redirect URI matches your app registration
   - Ensure proper API permissions are granted

2. **"Token refresh failed"**
   - User needs to re-authenticate
   - Check if refresh tokens are being stored properly

3. **"Invalid state parameter"**
   - Possible CSRF attack or session issues
   - Clear browser cookies and try again

### Debug Mode

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```
