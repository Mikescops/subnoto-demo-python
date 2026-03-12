"""Helpers to parse and format API error responses."""


def api_error_detail(resp) -> str:
    """
    Build a clear error string from an API response (status + JSON body).
    Handles Subnoto-style payloads: code/message/suggestion/documentationUrl,
    including when 'code' is a nested object.
    """
    status = getattr(resp, "status_code", None) or 0
    try:
        body = resp.json()
    except Exception:
        body = None

    if isinstance(body, dict):
        # SDK shape: prefer body["error"]["message"] then normalize other payloads
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        if err is body and "code" in body and isinstance(body["code"], dict):
            err = body["code"]

        code = err.get("code") if isinstance(err.get("code"), str) else None
        message = (
            (
                (body.get("error") or {}).get("message")
                if isinstance(body.get("error"), dict)
                else None
            )
            or err.get("message")
            or err.get("errorMessage")
            or err.get("description")
        )
        suggestion = err.get("suggestion")
        doc_url = err.get("documentationUrl")

        parts = [f"HTTP {status}"]
        if code:
            parts.append(code)
        if message:
            parts.append(message)
        if suggestion:
            parts.append(suggestion)
        if doc_url:
            parts.append(doc_url)

        if len(parts) > 1:
            return " - ".join(parts)

    text = getattr(resp, "text", None) or ""
    if text and len(text) < 500:
        return f"HTTP {status}: {text}"
    return f"HTTP {status}"
