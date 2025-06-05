import os
import json
import requests
from semantic_kernel.functions import kernel_function


class StackOverflowTool:
    """
    Tool for interacting with Stack Overflow.
    """

    @kernel_function(
        description="Fetches user info from Stack Overflow. If not authenticated, asks user to authenticate."
    )
    def get_user_info(self, **kwargs) -> str:
        """
        Checks for 'token' in kernel arguments.
        If not present, instructs agent to ask user to authenticate.
        If present, fetches user info from Stack Overflow /me endpoint.
        """
        token = kwargs["kwargs"].get("token", "")
        if not token:
            return (
                "Authentication required. Please authenticate by visiting: "
                "http://localhost:8001/auth/stackoverflow"
            )
        try:
            resp = requests.get(
                "https://api.stackexchange.com/2.3/me",
                params={
                    "site": "stackoverflow",
                    "access_token": token,
                    "key": os.getenv("STACKOVERFLOW_KEY", ""),
                },
                timeout=10,
            )
            if resp.status_code != 200:
                return json.dumps(
                    {
                        "error": f"Failed to fetch user info: {resp.status_code} {resp.text}"
                    }
                )
            return json.dumps(resp.json())
        except Exception as e:
            return json.dumps({"error": f"Exception: {str(e)}"})
