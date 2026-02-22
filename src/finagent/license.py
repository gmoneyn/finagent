"""License gating for premium FinAgent features."""

from __future__ import annotations

import json
import os


def check_license() -> dict:
    """Check whether a valid FinAgent license key is present.

    For MVP: any non-empty FINAGENT_LICENSE_KEY environment variable is accepted.
    Future: validate against the marketplace API.

    Returns:
        dict with at minimum ``valid`` (bool).
    """
    key = os.environ.get("FINAGENT_LICENSE_KEY", "").strip()
    if key:
        return {"valid": True, "key": key}
    return {"valid": False}


def require_license(tool_name: str) -> str | None:
    """Gate a tool behind a license check.

    Args:
        tool_name: Name of the tool being gated (for the error message).

    Returns:
        ``None`` if the license is valid (caller should proceed).
        A JSON error string if the license is missing/invalid (caller should
        return this string directly to the MCP client).
    """
    result = check_license()
    if result["valid"]:
        return None

    return json.dumps({
        "error": "premium_required",
        "message": (
            f"The '{tool_name}' tool requires a FinAgent Premium license. "
            "Set the FINAGENT_LICENSE_KEY environment variable to unlock it. "
            "Get your key at https://finagent.dev/pricing"
        ),
    })
