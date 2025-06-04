import json
import signal
import logging
from typing import Optional
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import gradio as gr
from app import demo
from starlette.responses import RedirectResponse
from starlette_session import SessionMiddleware, ISessionBackend
import os

from dotenv import load_dotenv
from auth_msal import get_msal_auth, get_current_user, require_auth, get_access_token

# Load environment variables from .env file at the start of your script
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Azure AI Agent Service", version="1.0.0")

class SessionStore(ISessionBackend):
    """Custom session store in-memory."""
    def __init__(self):
        self.sessions = {}

    async def get(self, key: str) -> Optional[dict]:
        return self.sessions.get(key) or {}

    async def set(self, key: str, value: dict, exp: Optional[int]) -> Optional[str]:
        self.sessions[key] = value

    async def delete(self, key: str) -> None:
        if key in self.sessions:
            del self.sessions[key]

# IMPORTANT: Add SessionMiddleware FIRST so request.session is always available
SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    cookie_name="gradio_session",
    backend_type="custom",
    custom_session_backend=SessionStore(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_user_name(request: Request) -> Optional[str]:
    """Get username for Gradio auth dependency."""
    # At this point, middleware has already ensured user is authenticated
    user = get_current_user(request)
    if user:
        return user.get("name") or user.get("email")
    return None


@app.get("/login")
async def login(request: Request):
    """Initiate Azure AD login."""
    # Generate a state parameter for security
    import uuid
    state = str(uuid.uuid4())
    request.session["oauth_state"] = state
    
    # Get authorization URL
    auth_url = get_msal_auth().get_auth_url(state=state)
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle Azure AD callback."""
    try:
        # Verify state parameter
        state = request.query_params.get("state")
        session_state = request.session.get("oauth_state")
        
        if not state or state != session_state:
            logger.warning("Invalid state parameter in auth callback")
            return RedirectResponse(url="/?error=invalid_state")
        
        # Get authorization code
        code = request.query_params.get("code")
        if not code:
            error = request.query_params.get("error")
            logger.error(f"Authorization failed: {error}")
            return RedirectResponse(url=f"/?error={error}")
        
        # Exchange code for token
        token_data = get_msal_auth().acquire_token_by_auth_code(code, state)
        
        user_obj = get_msal_auth().get_user_from_token(token_data["access_token"])

        # Store token and user info in session
        request.session["user"] = user_obj
        request.session["token_data"] = token_data
        logger.info(f"User authenticated: {request.session['user']['email']}")

        # Clear state
        request.session.pop("oauth_state", None)
        
        return RedirectResponse(url="/gradio")
        
    except HTTPException as e:
        logger.error(f"Authentication error: {e.detail}")
        return RedirectResponse(url=f"/?error=auth_failed")
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        return RedirectResponse(url="/?error=unexpected_error")


@app.get("/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    user = request.session.get("user")
    if user:
        logger.info(f"User logged out: {user.get('email', 'unknown')}")
    
    request.session.clear()
    
    # Redirect to Azure AD logout for complete logout
    logout_url = f"https://login.microsoftonline.com/{get_msal_auth().tenant_id}/oauth2/v2.0/logout"
    logout_url += f"?post_logout_redirect_uri={request.url_for('home')}"
    
    return RedirectResponse(url=logout_url)


@app.get("/")
async def home(request: Request):
    """Home page with automatic login redirect."""
    user = get_current_user(request)
    error = request.query_params.get("error")
    
    if error:
        return JSONResponse(
            content={"error": f"Authentication error: {error}"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    if user:
        # User is authenticated, redirect to Gradio app
        return RedirectResponse(url="/gradio")
    else:
        # User is not authenticated, redirect to login
        return RedirectResponse(url="/login")

@app.get("/auth/status")
async def auth_status(request: Request):
    """Get authentication status (for API clients)."""
    user = get_current_user(request)
    if user:
        return JSONResponse(content={
            "authenticated": True,
            "user": user,
            "message": "User is authenticated"
        })
    else:
        return JSONResponse(
            content={
                "authenticated": False,
                "login_url": "/login",
                "message": "Authentication required"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

@app.get("/health")
async def health_check(request: Request):
    return JSONResponse(content={"status": "ok"})

@app.get("/ready")
async def ready_check(request: Request):
    if demo:
        return JSONResponse(content={"status": "ready"})
    return JSONResponse(
        content={"status": "not ready"}, 
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )

# --- Gradio Sub-App for Shared Session ---
from fastapi import FastAPI as GradioFastAPI

gradio_sub_app = GradioFastAPI()
# Do NOT add SessionMiddleware here! Only the main app should have it.
gr.mount_gradio_app(gradio_sub_app, demo, path="/", auth_dependency=get_user_name)
app.mount("/gradio", gradio_sub_app)

# If running with uvicorn:
# uvicorn main:app --host 0.0.0.0 --port 8000


def signal_handler(sig, frame):
    print("Shutting down gracefully...")
    raise SystemExit(0)


signal.signal(signal.SIGINT, signal_handler)

def get_json_size_bytes(obj) -> int:
    """Return the size in bytes of the JSON-serialized object."""
    return len(json.dumps(obj, separators=(',', ':')).encode('utf-8'))