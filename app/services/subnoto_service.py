"""Subnoto API: create envelope from PDF, add recipient/blocks, send, create iframe token."""

import logging
from io import BytesIO

try:
    from subnoto_api_client import SubnotoConfig, SubnotoSyncClient
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "subnoto_api_client not found. Install with: pip install subnoto-api-client (use the same Python that runs this app)."
    ) from e

from app import config
from app.services.api_error import api_error_detail

logger = logging.getLogger(__name__)


def get_whoami() -> dict:
    """Call Subnoto /public/utils/whoami and return apiBaseUrl, teamUuid, teamName, ownerEmail, ownerUuid, accessKey (or error)."""
    logger.info("whoami: calling Subnoto API at %s", config.SUBNOTO_BASE_URL)
    cfg = SubnotoConfig(
        api_base_url=config.SUBNOTO_BASE_URL,
        access_key=config.SUBNOTO_ACCESS_KEY,
        secret_key=config.SUBNOTO_SECRET_KEY,
        unattested=config.SUBNOTO_UNATTESTED,
    )
    try:
        with SubnotoSyncClient(cfg) as client:
            resp = client.post("/public/utils/whoami", json={})
            resp.raise_for_status()
            data = resp.json()
            logger.info("whoami: success team=%s owner=%s", data.get("teamName"), data.get("ownerEmail"))
            return {
                "apiBaseUrl": config.SUBNOTO_BASE_URL,
                "teamUuid": data.get("teamUuid", ""),
                "teamName": data.get("teamName", ""),
                "ownerEmail": data.get("ownerEmail", ""),
                "ownerUuid": data.get("ownerUuid", ""),
                "accessKey": config.SUBNOTO_ACCESS_KEY,
            }
    except Exception as e:
        logger.exception("whoami: Subnoto API failed: %s", e)
        return {"error": str(e)}


def _embed_sign_url(token: str) -> str:
    base = config.SUBNOTO_EMBED_BASE_URL.rstrip("/")
    # If base uses host.docker.internal, use localhost for the iframe so the host browser can load it
    if "host.docker.internal" in base:
        base = base.replace("host.docker.internal", "localhost")
    url = f"{base}/embeds/sign#t={token}"
    logger.info("embed iframe URL base: %s", base)
    return url


def create_envelope_and_iframe_url(
    pdf_bytes: bytes,
    envelope_title: str,
    signer_email: str,
    signer_firstname: str,
    signer_lastname: str,
) -> str:
    """
    Create envelope from PDF with detectSmartAnchors; recipients and blocks come from the PDF.
    Send with distributionMethod=none, then create iframe token. Returns the embed signing URL.
    """
    cfg = SubnotoConfig(
        api_base_url=config.SUBNOTO_BASE_URL,
        access_key=config.SUBNOTO_ACCESS_KEY,
        secret_key=config.SUBNOTO_SECRET_KEY,
        unattested=config.SUBNOTO_UNATTESTED,
    )
    with SubnotoSyncClient(cfg) as client:
        # 1. Create envelope from file via _client (data= + files= as in official SDK example)
        files = {"file": ("quote.pdf", BytesIO(pdf_bytes), "application/pdf")}
        data = {
            "workspaceUuid": config.WORKSPACE_UUID,
            "envelopeTitle": envelope_title,
            "detectSmartAnchors": "true",
        }
        resp = client._client.post(
            "/public/envelope/create-from-file",
            data=data,
            files=files,
        )
        if not resp.is_success:
            raise ValueError(api_error_detail(resp))
        create_result = resp.json()
        envelope_uuid = create_result["envelopeUuid"]

        # 2. Send with distributionMethod=none (no email; signing via iframe)
        # Recipients and signature blocks come from Smart Anchors in the PDF; no add-recipients/add-blocks.
        r = client.post(
            "/public/envelope/send",
            json={
                "workspaceUuid": config.WORKSPACE_UUID,
                "envelopeUuid": envelope_uuid,
                "distributionMethod": "none",
            },
        )
        if not r.is_success:
            raise ValueError(f"send: {api_error_detail(r)}")

        # 3. Create iframe token for the signer
        r = client.post(
            "/public/authentication/create-iframe-token",
            json={
                "workspaceUuid": config.WORKSPACE_UUID,
                "envelopeUuid": envelope_uuid,
                "signerEmail": signer_email,
            },
        )
        if not r.is_success:
            raise ValueError(f"create-iframe-token: {api_error_detail(r)}")
        token_body = r.json()
        iframe_token = token_body.get("iframeToken")
        if not iframe_token:
            raise ValueError("create-iframe-token did not return iframeToken")

        return _embed_sign_url(iframe_token)
