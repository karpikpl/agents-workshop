"""
MSAL authentication module for Azure Entra ID integration.
Provides proper token management, refresh handling, and user context.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import msal
from fastapi import Request, HTTPException, status
import jwt

logger = logging.getLogger(__name__)

class MSALAuth:
    def __init__(self):
        # Configuration from environment variables
        self.client_id = os.getenv("AAD_CLIENT_ID")
        self.client_secret = os.getenv("AAD_CLIENT_SECRET") 
        self.tenant_id = os.getenv("AAD_TENANT_ID")
        self.redirect_uri = os.getenv("AAD_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # Validate required config
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Missing required Azure AD configuration. Please set AAD_CLIENT_ID, AAD_CLIENT_SECRET, and AAD_TENANT_ID")
        
        # Authority URL
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        # Scopes for Azure services
        self.scopes = [
            # "openid",
            # "profile", 
            "email",
            # "https://cognitiveservices.azure.com/.default",  # For Azure AI services
            # "https://management.azure.com/.default"  # For Azure Resource Manager
        ]
        
        # Create MSAL confidential client
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            token_cache=None  # We'll use session-based storage
        )
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate authorization URL for login."""
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        return auth_url
    
    def acquire_token_by_auth_code(self, auth_code: str, state: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        result = self.app.acquire_token_by_authorization_code(
            code=auth_code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            logger.error(f"Token acquisition failed: {result.get('error_description', result.get('error'))}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {result.get('error_description', 'Unknown error')}"
            )
        
        return result
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        try:
            result = self.app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes
            )
            
            if "error" in result:
                logger.warning(f"Token refresh failed: {result.get('error_description')}")
                return None
            
            return result
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return None
    
    def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from access token."""
        try:
            # Decode token without verification for user info (already validated by MSAL)
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            
            user_info = {
                "id": decoded.get("oid"),  # Object ID
                "name": decoded.get("name"),
                "email": decoded.get("email") or decoded.get("preferred_username"),
                "tenant_id": decoded.get("tid"),
                "roles": decoded.get("roles", []),
                "groups": decoded.get("groups", [])
            }
            
            return user_info
        except Exception as e:
            logger.error(f"Failed to decode user token: {str(e)}")
            return None
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if access token is expired."""
        if not token_data or "expires_in" not in token_data:
            return True
        
        # Check if token expires in next 5 minutes (buffer for safety)
        expires_at = token_data.get("expires_at", 0)
        if expires_at == 0:
            # If expires_at is not set, calculate it from expires_in
            issued_at = token_data.get("issued_at", datetime.now().timestamp())
            expires_in = token_data.get("expires_in", 3600)
            expires_at = issued_at + expires_in
            token_data["expires_at"] = expires_at
        
        buffer_time = 300  # 5 minutes
        return datetime.now().timestamp() + buffer_time >= expires_at
    
    def ensure_valid_token(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ensure we have a valid access token, refresh if needed."""
        token_data = session.get("token_data")
        
        if not token_data:
            return None
        
        # If token is not expired, return current token
        if not self.is_token_expired(token_data):
            return token_data
        
        # Try to refresh token
        refresh_token = token_data.get("refresh_token")
        if refresh_token:
            logger.info("Refreshing expired access token")
            new_token_data = self.refresh_token(refresh_token)
            
            if new_token_data:
                # Update session with new token data
                session["token_data"] = new_token_data
                session["user"] = self.get_user_from_token(new_token_data["access_token"])
                return new_token_data
        
        # Token refresh failed, user needs to re-authenticate
        logger.warning("Token refresh failed, clearing session")
        session.clear()
        return None


# Global MSAL instance - will be initialized when needed
msal_auth = None

def get_msal_auth() -> MSALAuth:
    """Get or create the global MSAL authentication instance."""
    global msal_auth
    if msal_auth is None:
        msal_auth = MSALAuth()
    return msal_auth


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session."""
    try:
        # Ensure we have a valid token
        token_data = get_msal_auth().ensure_valid_token(request.session)
        
        if not token_data:
            return None
        
        user = request.session.get("user")
        if user:
            return user
        
        # Extract user from token if not in session
        access_token = token_data.get("access_token")
        if access_token:
            user = get_msal_auth().get_user_from_token(access_token)
            request.session["user"] = user
            return user
        
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None


def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication, raise exception if not authenticated."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def get_access_token(request: Request) -> Optional[str]:
    """Get current access token for API calls."""
    token_data = get_msal_auth().ensure_valid_token(request.session)
    return token_data.get("access_token") if token_data else None
