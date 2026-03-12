"""Subnoto API: create envelope from PDF, add recipient/blocks, send, create iframe token."""

import logging
from io import BytesIO

try:
    from subnoto_api_client import (
        SubnotoConfig,
        SubnotoSyncClient,
        SubnotoError,
        get_error_code,
    )
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "subnoto_api_client not found. Install with: pip install subnoto-api-client (use the same Python that runs this app)."
    ) from e

from app import config
from app.services.api_error import api_error_detail

logger = logging.getLogger(__name__)


def _raise_subnoto_error(resp, context: str) -> None:
    """Build message from response body (SDK shape) and raise SubnotoError."""
    status = getattr(resp, "status_code", 0)
    try:
        body = resp.json()
    except Exception:
        body = {}
    if isinstance(body, dict):
        msg = body.get("error", {}).get("message", str(body)) if isinstance(body.get("error"), dict) else body.get("message", "")
        if not msg:
            msg = str(body)
        code = get_error_code(body)
        if code:
            msg = f"{code}: {msg}"
    else:
        msg = getattr(resp, "text", None) or f"HTTP {status}"
    raise SubnotoError(f"{context}: {msg}", status)


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
        msg = str(e)
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                body = resp.json()
                if isinstance(body, dict):
                    msg = body.get("error", {}).get("message", str(body)) if isinstance(body.get("error"), dict) else body.get("message", msg)
                    code = get_error_code(body)
                    if code:
                        msg = f"{code}: {msg}"
            except Exception:
                pass
        return {"error": msg}


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
        # 1. Create envelope from file (public client supports multipart)
        files = {"file": ("quote.pdf", BytesIO(pdf_bytes), "application/pdf")}
        data = {
            "workspaceUuid": config.WORKSPACE_UUID,
            "envelopeTitle": envelope_title,
            "detectSmartAnchors": "true",
        }
        resp = client.post(
            "/public/envelope/create-from-file",
            data=data,
            files=files,
        )
        if not resp.is_success:
            _raise_subnoto_error(resp, "create-from-file")
        create_result = resp.json()
        envelope_uuid = create_result["envelopeUuid"]

        # 1b. For each recipient detected via Smart Anchors, enable email verification
        smart_anchor = create_result.get("smartAnchor")
        smart_anchor_recipients = (
            smart_anchor.get("recipients") if isinstance(smart_anchor, dict) else []
        ) or []
        for recipient in smart_anchor_recipients:
            if isinstance(recipient, str):
                recipient_email = recipient
                recipient_role = "signer"
            elif isinstance(recipient, dict):
                recipient_email = recipient.get("email")
                recipient_role = recipient.get("role", "signer")
            else:
                logger.warning("smartAnchor recipient invalid type: %s", type(recipient))
                continue
            if not recipient_email:
                logger.warning("smartAnchor recipient missing email: %s", recipient)
                continue
            # API requires: email, role, and updates (object with verificationType)
            update_payload = {
                "workspaceUuid": config.WORKSPACE_UUID,
                "envelopeUuid": envelope_uuid,
                "email": recipient_email,
                "role": recipient_role,
                "updates": {"verificationType": "email"},
            }
            r_update = client.post(
                "/public/envelope/update-recipient",
                json=update_payload,
            )
            if not r_update.is_success:
                try:
                    body = r_update.json()
                    code = get_error_code(body) if isinstance(body, dict) else None
                    detail = code or api_error_detail(r_update)
                except Exception:
                    detail = api_error_detail(r_update)
                logger.warning(
                    "update-recipient failed for recipient %s: %s",
                    recipient_email,
                    detail,
                )
            else:
                logger.info(
                    "update-recipient enabled email verification for %s",
                    recipient_email,
                )

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
            _raise_subnoto_error(r, "send")

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
            _raise_subnoto_error(r, "create-iframe-token")
        token_body = r.json()
        iframe_token = token_body.get("iframeToken")
        if not iframe_token:
            raise SubnotoError("create-iframe-token did not return iframeToken", r.status_code)

        return _embed_sign_url(iframe_token)
