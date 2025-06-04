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
   - Accessing `/gradio` automatically redirects to `/login`
   - Protected routes require authentication

2. **Authentication Process**:
   - `/login` redirects to Azure Entra ID
   - After successful authentication, users are redirected to `/gradio`
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

2. Update `.env` with your values:
   ```env
   # Azure Entra ID Configuration
   AAD_CLIENT_ID=your-application-client-id
   AAD_CLIENT_SECRET=your-client-secret-value  
   AAD_TENANT_ID=your-tenant-id
   AAD_REDIRECT_URI=http://localhost:8000/auth/callback

   # Session Security
   SECRET_KEY=your-random-secret-key-for-sessions

   # Azure AI Foundry
   AZURE_AI_FOUNDRY_CONNECTION_STRING=your-ai-foundry-connection-string
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=your-chat-deployment-name
   AZURE_OPENAI_API_VERSION=2024-10-21

   # Optional: Application Insights
   APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection
   ```

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

## Testing the Authentication Flow

### Automated Testing

Run the authentication flow test to verify redirects work correctly:

```bash
# Start the application first
uvicorn main:app --host 0.0.0.0 --port 8501 &

# Run the test script
python test_auth_flow.py
```

### Manual Testing

1. **Start the application**:
   ```bash
   ./start.sh
   ```

2. **Test authentication flow**:
   - Visit `http://localhost:8501/` - should redirect to login
   - Visit `http://localhost:8501/gradio` - should redirect to login
   - Visit `http://localhost:8501/auth/status` - should return 401 Unauthorized
   - Visit `http://localhost:8501/health` - should return OK (no auth required)

3. **Complete authentication**:
   - Visit `http://localhost:8501/login` - redirects to Azure Entra ID
   - Complete Azure authentication
   - Should be redirected back to `/gradio` with full access

### Expected Behavior

- ✅ **Unauthenticated users**: Automatically redirected to login
- ✅ **Protected routes**: `/gradio` and related paths require authentication
- ✅ **Public routes**: `/health`, `/ready` work without authentication
- ✅ **Post-authentication**: Users are redirected to the Gradio application
- ✅ **Session management**: Authentication persists across requests
- ✅ **Logout**: Clears both local and Azure sessions

## Authentication Flow

1. **User visits** `http://localhost:8000/`
2. **If not authenticated**, they see login information
3. **Click login** redirects to Azure Entra ID
4. **After authentication**, user is redirected back to the app
5. **Access the chat interface** at `http://localhost:8000/gradio`

## API Endpoints

- `GET /` - Home page with authentication status
- `GET /login` - Initiate Azure AD login
- `GET /auth/callback` - Handle Azure AD callback
- `GET /logout` - Logout and clear session
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check
- `/gradio` - Main chat interface (requires authentication)

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
