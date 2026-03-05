# Getting started

## Prerequisites

- **Python** (3.10+)
- **pip** (or use a virtual environment)
- A Subnoto workspace and API credentials

## Setup

1. **Clone and install**

    ```bash
    pip install -r requirements.txt
    ```

    Or use a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate   # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

2. **Environment variables**

    Copy `.env.example` to `.env` in the project root and fill in your credentials. All variable names and optional ones are listed in `.env.example`. Required:

    - `SUBNOTO_ACCESS_KEY`: API access key
    - `SUBNOTO_SECRET_KEY`: API secret key
    - `WORKSPACE_UUID`: Workspace UUID

    Optional:

    - `SUBNOTO_BASE_URL`: Subnoto API base URL (default: `https://enclave.subnoto.com`)
    - `SUBNOTO_EMBED_BASE_URL`: Base URL for the embed iframe (default: `https://app.subnoto.com`). The signing iframe URL is `{SUBNOTO_EMBED_BASE_URL}/embeds/sign#t={iframeToken}`.
    - `SUBNOTO_UNATTESTED`: Set to `true` for unattested or dev usage if required
    - `SUBNOTO_DEMO_SIGNER_EMAIL`: Default signer email when the quote form does not provide one (default: `demo@example.com`)

    The demo uses the form’s recipient email as the signer, or falls back to `SUBNOTO_DEMO_SIGNER_EMAIL`.

3. **Run the app**

    ```bash
    python run.py
    ```

    Open http://localhost:8000.

## Demo

- **Quote** (`/`): Fill in the quote form (title, amount, recipient name and email, etc.). Click "Send for signature". The app builds a PDF with ReportLab, creates an envelope with Smart Anchor detection (recipient and signature block come from the PDF), sends with no email, and opens the signing iframe.

No sample PDF file is required; the quote PDF is generated from the form.
