# Customer implementation tutorial (Python)

This guide explains how to implement the same flow on your side: set up the API client, create an envelope from a PDF with Smart Anchors, and embed the signing iframe.

Reference code in this repo:

- **Config**: `app/config.py`
- **Subnoto service** (whoami, create envelope, iframe token): `app/services/subnoto_service.py`
- **Quote API** (form → PDF → envelope → iframe URL): `app/routes/quotes.py`

---

## 1. Setting up

**Environment variables**

- `SUBNOTO_BASE_URL`: API base URL (e.g. `https://enclave.subnoto.com`), optional (default: `https://enclave.subnoto.com`)
- `SUBNOTO_ACCESS_KEY`: API access key
- `SUBNOTO_SECRET_KEY`: API secret key
- `WORKSPACE_UUID`: Workspace UUID
- `SUBNOTO_UNATTESTED`: Set to `true` for unattested/dev usage if required (optional)

**API client**

Install the Subnoto Python client and create the config in your server-side code:

```bash
pip install subnoto-api-client
```

```python
from subnoto_api_client import SubnotoConfig, SubnotoSyncClient

cfg = SubnotoConfig(
    api_base_url=os.environ.get("SUBNOTO_BASE_URL", "https://enclave.subnoto.com"),
    access_key=os.environ["SUBNOTO_ACCESS_KEY"],
    secret_key=os.environ["SUBNOTO_SECRET_KEY"],
    unattested=os.environ.get("SUBNOTO_UNATTESTED", "").lower() in ("1", "true", "yes"),
)
workspace_uuid = os.environ["WORKSPACE_UUID"]
```

Use `SubnotoSyncClient` as a context manager when calling the API:

```python
with SubnotoSyncClient(cfg) as client:
    # client.post("/path", json={...}), etc.
```

Make sure the required env vars are set before calling the API. See `app/config.py` for the exact loading logic.

---

## 2. Creating an envelope from a PDF with Smart Anchors

If your PDF already contains **Smart Anchors** (e.g. `{{ signer@example.com | signature | 180 | 60 }}`), you can create an envelope without calling add-recipients or add-blocks. The API detects recipients and blocks from the PDF.

**1. Create envelope from file with Smart Anchor detection**

Use multipart form data: `workspaceUuid`, `envelopeTitle`, `detectSmartAnchors`, and the PDF file.

```python
from io import BytesIO

files = {"file": ("document.pdf", BytesIO(pdf_bytes), "application/pdf")}
data = {
    "workspaceUuid": workspace_uuid,
    "envelopeTitle": "My quote",
    "detectSmartAnchors": "true",
}

with SubnotoSyncClient(cfg) as client:
    resp = client._client.post(
        "/public/envelope/create-from-file",
        data=data,
        files=files,
    )
    if not resp.is_success:
        raise ValueError(...)  # handle error from resp
    create_result = resp.json()
    envelope_uuid = create_result["envelopeUuid"]
```

**2. Send with no email (signing via iframe)**

```python
r = client.post(
    "/public/envelope/send",
    json={
        "workspaceUuid": workspace_uuid,
        "envelopeUuid": envelope_uuid,
        "distributionMethod": "none",
    },
)
if not r.is_success:
    raise ValueError(...)
```

You do not call add-recipients or add-blocks. See `app/services/subnoto_service.py` (`create_envelope_and_iframe_url`) for the full flow and error handling.

---

## 3. Embedding signing (iframe token and URL)

To show the signing experience in an iframe, create a one-time iframe token, then build the embed URL.

**Create iframe token**

```python
r = client.post(
    "/public/authentication/create-iframe-token",
    json={
        "workspaceUuid": workspace_uuid,
        "envelopeUuid": envelope_uuid,
        "signerEmail": "signer@example.com",  # must match a recipient on the envelope
    },
)
if not r.is_success:
    raise ValueError(...)
token_body = r.json()
iframe_token = token_body.get("iframeToken")
if not iframe_token:
    raise ValueError("create-iframe-token did not return iframeToken")
```

**Build iframe URL**

Base URL is usually `https://app.subnoto.com` (or set via `SUBNOTO_EMBED_BASE_URL`). Path is `/embeds/sign`; put the token in the URL hash:

```python
embed_base_url = os.environ.get("SUBNOTO_EMBED_BASE_URL", "https://app.subnoto.com").rstrip("/")
iframe_url = f"{embed_base_url}/embeds/sign#t={iframe_token}"
```

See `_embed_sign_url` in `app/services/subnoto_service.py` for the exact logic (including the `host.docker.internal` → `localhost` replacement when running in Docker).

**Embed in the page**

```html
<iframe src="{{ iframe_url }}" title="Subnoto signing" allow="fullscreen" allowfullscreen></iframe>
```

Your backend returns `iframeUrl` to the frontend, which sets it as the iframe `src`. See `app/routes/quotes.py` and `app/static/js/app.js` for how this demo does it.

---

## 4. Optional: whoami (header / default signer)

To display API/team info or use the API key owner as a default signer, call whoami:

```python
resp = client.post("/public/utils/whoami", json={})
resp.raise_for_status()
data = resp.json()
# data: teamUuid, teamName, ownerEmail, ownerUuid, ...
```

See `get_whoami()` in `app/services/subnoto_service.py` and the `/api/whoami` route in `app/routes/quotes.py`.

---

## Summary

| Goal                          | Endpoint / method                                                          | Reference in repo                    |
| ----------------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
| Create client                 | `SubnotoConfig` + `SubnotoSyncClient(cfg)`                                 | `app/config.py`, `app/services/subnoto_service.py` |
| Create from file (Smart Anchors) | `POST /public/envelope/create-from-file` (with `detectSmartAnchors: "true"`) | `app/services/subnoto_service.py`    |
| Send (no email)               | `POST /public/envelope/send` with `distributionMethod: "none"`             | same                                 |
| Iframe token                 | `POST /public/authentication/create-iframe-token`                          | same                                 |
| Embed URL                    | `{SUBNOTO_EMBED_BASE_URL}/embeds/sign#t={iframeToken}`                      | `_embed_sign_url` in subnoto_service |
| Whoami                       | `POST /public/utils/whoami`                                                | `get_whoami()` in subnoto_service    |
