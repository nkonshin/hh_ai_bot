import json
import os
from pathlib import Path

BASE_URL = "https://api.hh.ru"
USER_AGENT = "HH-MCP-Server/1.0"

# Default path where hh-applicant-tool stores its config
HH_TOOL_CONFIG = Path.home() / ".config" / "hh-applicant-tool" / "config" / "config.json"


def get_access_token() -> str:
    """Get hh.ru access token.

    Priority:
    1. HH_ACCESS_TOKEN environment variable
    2. hh-applicant-tool config file
    """
    token = os.environ.get("HH_ACCESS_TOKEN")
    if token:
        return token

    config_path = Path(
        os.environ.get("HH_CONFIG_DIR", HH_TOOL_CONFIG.parent)
    ) / "config.json"

    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
        token = data.get("access_token")
        if token:
            return token

    raise RuntimeError(
        "No hh.ru access token found. Set HH_ACCESS_TOKEN env variable "
        "or install and configure hh-applicant-tool."
    )
