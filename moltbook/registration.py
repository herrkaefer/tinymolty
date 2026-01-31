"""
Moltbook agent registration module
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class RegistrationResponse:
    """Registration response data"""
    api_key: str
    agent_name: str
    claim_url: str
    verification_code: str


async def register_agent(
    name: str,
    description: str,
    base_url: str = "https://www.moltbook.com/api/v1"
) -> RegistrationResponse:
    """
    Register a new Moltbook agent

    Args:
        name: Agent name
        description: Agent description
        base_url: API base URL

    Returns:
        RegistrationResponse containing api_key, claim_url, verification_code

    Raises:
        httpx.HTTPError: When registration fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/agents/register",
            json={
                "name": name,
                "description": description
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        data = response.json()

        # API response structure:
        # {
        #   "success": true,
        #   "agent": {
        #     "id": "...",
        #     "name": "...",
        #     "api_key": "moltbook_sk_...",
        #     "claim_url": "https://...",
        #     "verification_code": "...",
        #     ...
        #   },
        #   ...
        # }

        agent_data = data.get("agent", {})

        return RegistrationResponse(
            api_key=agent_data.get("api_key", ""),
            agent_name=agent_data.get("name", name),
            claim_url=agent_data.get("claim_url", ""),
            verification_code=agent_data.get("verification_code", "")
        )


async def check_claim_status(
    api_key: str,
    base_url: str = "https://www.moltbook.com/api/v1"
) -> dict:
    """
    Check agent claim status

    Args:
        api_key: API Key
        base_url: API base URL

    Returns:
        Status information
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{base_url}/agents/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()
        return response.json()


def save_credentials(
    api_key: str,
    agent_name: str,
    credentials_path: str | Path = "~/.config/moltbook/credentials.json"
) -> Path:
    """
    Save credentials to file

    Args:
        api_key: API Key
        agent_name: Agent name
        credentials_path: Credentials file path

    Returns:
        Saved file path
    """
    path = Path(credentials_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    credentials = {
        "api_key": api_key,
        "agent_name": agent_name
    }

    path.write_text(json.dumps(credentials, indent=2))
    path.chmod(0o600)

    return path


def load_credentials(
    credentials_path: str | Path = "~/.config/moltbook/credentials.json"
) -> dict | None:
    """
    Load credentials from file

    Args:
        credentials_path: Credentials file path

    Returns:
        Credentials dict, or None if file doesn't exist
    """
    path = Path(credentials_path).expanduser()
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
