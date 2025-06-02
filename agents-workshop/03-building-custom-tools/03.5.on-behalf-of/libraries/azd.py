import json
import logging
import os
import subprocess
from dotenv import load_dotenv
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv(override=True)
is_dev = os.environ.get("DEVELOPMENT", "False").lower() in ("true", "1", "yes")
logger.info(f"Running in {'development' if is_dev else 'production'} mode")


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv"""
    result = subprocess.run(
        "azd env list -o json", shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception("Error loading azd env")
    env_json = json.loads(result.stdout)
    env_file_path = None
    for entry in env_json:
        if entry["IsDefault"]:
            env_file_path = entry["DotEnvPath"]
    if not env_file_path:
        raise Exception("No default azd env file found")
    logger.info(f"Loading azd env from {env_file_path}")
    load_dotenv(env_file_path, override=True)
