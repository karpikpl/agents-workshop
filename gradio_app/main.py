import signal
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
from app import demo
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
import os

from dotenv import load_dotenv

# Load environment variables from .env file at the start of your script
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure Entra ID (AAD) config - fill in your values
TENANT_ID = os.getenv("AAD_TENANT_ID", "<your-tenant-id>")
CLIENT_ID = os.getenv("AAD_CLIENT_ID", "<your-client-id>")
CLIENT_SECRET = os.getenv("AAD_CLIENT_SECRET", "<your-client-secret>")
REDIRECT_URI = os.getenv("AAD_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Authority and endpoints
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"

# Scopes for OpenID Connect
SCOPES = ["openid", "profile", "email"]

# Add session middleware for OAuth
SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configure OAuth for Entra ID
config_data = {
    "AAD_CLIENT_ID": CLIENT_ID,
    "AAD_CLIENT_SECRET": CLIENT_SECRET,
}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name="aad",
    server_metadata_url=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Only keep session-based OAuth logic and Gradio auth_dependency


def get_user(request: Request):
    user = request.session.get("user")
    if user:
        return user["name"]
    return None


@app.route("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.aad.authorize_redirect(request, redirect_uri)


@app.route("/auth")
async def auth(request: Request):
    try:
        token = await oauth.aad.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url="/")
    request.session["user"] = dict(token)["userinfo"]
    return RedirectResponse(url="/")


@app.route("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


# Mount Gradio app with Entra ID auth
# app = gr.mount_gradio_app(app, demo, path="/", auth_dependency=get_user)
app = gr.mount_gradio_app(app, demo, path="/")

# If running with uvicorn:
# uvicorn main:app --host 0.0.0.0 --port 8000


def signal_handler(sig, frame):
    print("Shutting down gracefully...")
    raise SystemExit(0)


signal.signal(signal.SIGINT, signal_handler)
