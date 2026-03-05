"""App configuration from environment variables."""

import os


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required env: {key}")
    return value


SUBNOTO_BASE_URL = os.environ.get("SUBNOTO_BASE_URL", "https://enclave.subnoto.com")
SUBNOTO_ACCESS_KEY = _require("SUBNOTO_ACCESS_KEY")
SUBNOTO_SECRET_KEY = _require("SUBNOTO_SECRET_KEY")
WORKSPACE_UUID = _require("WORKSPACE_UUID")
SUBNOTO_EMBED_BASE_URL = os.environ.get("SUBNOTO_EMBED_BASE_URL", "https://app.subnoto.com")
SUBNOTO_UNATTESTED = os.environ.get("SUBNOTO_UNATTESTED", "").lower() in ("1", "true", "yes")
SUBNOTO_DEMO_SIGNER_EMAIL = os.environ.get("SUBNOTO_DEMO_SIGNER_EMAIL", "demo@example.com")
