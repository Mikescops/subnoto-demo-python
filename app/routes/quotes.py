"""Quote form and create API."""

import logging

from flask import Blueprint, jsonify, render_template, request

from app import config
from app.models.quote import QuoteData
from app.services import build_quote_pdf, create_envelope_and_iframe_url, get_whoami

logger = logging.getLogger(__name__)
quotes_bp = Blueprint("quotes", __name__)


@quotes_bp.route("/")
def index():
    return render_template("index.html")


@quotes_bp.route("/api/whoami", methods=["GET"])
def whoami():
    """Return Subnoto whoami (team, owner email, API base URL) for header and default signer."""
    logger.info("GET /api/whoami")
    result = get_whoami()
    if "error" in result:
        logger.warning("GET /api/whoami -> error: %s", result["error"])
    return jsonify(result)


@quotes_bp.route("/api/quotes/create", methods=["POST"])
def create_quote():
    data = request.get_json(force=True, silent=True) or {}
    logger.info("POST /api/quotes/create payload keys=%s", list(data.keys()))
    quote = QuoteData.from_json(data)
    signer_email = quote.email or config.SUBNOTO_DEMO_SIGNER_EMAIL
    if not signer_email:
        logger.warning("POST /api/quotes/create: missing recipient email")
        return jsonify({"error": "Recipient email is required"}), 400
    try:
        pdf_bytes = build_quote_pdf(quote)
        logger.info("POST /api/quotes/create: PDF built (%s bytes), calling Subnoto", len(pdf_bytes))
        iframe_url = create_envelope_and_iframe_url(
            pdf_bytes=pdf_bytes,
            envelope_title=quote.title,
            signer_email=signer_email,
            signer_firstname=quote.firstname,
            signer_lastname=quote.lastname,
        )
        logger.info("POST /api/quotes/create: success")
        return jsonify({"iframeUrl": iframe_url})
    except Exception as e:
        logger.exception("POST /api/quotes/create failed: %s", e)
        return jsonify({"error": str(e)}), 500
