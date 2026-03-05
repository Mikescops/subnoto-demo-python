# Subnoto SDK demo (Python)

This app shows how to use the Subnoto API from Python and embed the signing flow in your own product. You create an envelope from a quote PDF (built with Smart Anchors), send it without email, and open the signing experience in an iframe.

## Demo

- **Quote** (`/`): Fill in a quote form, then send for signature. The app builds a PDF with ReportLab, creates an envelope with Smart Anchors (recipient and signature block are detected from the PDF), sends with no email, and opens signing in an iframe.

## Quick start

**Requirements:** Python 3.11+ and pip (or venv). Details are in [docs/getting-started.md](docs/getting-started.md).

1. **Environment**: Copy `.env.example` to `.env` in the project root and set your Subnoto credentials:
    - `SUBNOTO_ACCESS_KEY`, `SUBNOTO_SECRET_KEY`, `WORKSPACE_UUID`
    - Full list and optional variables: [docs/getting-started.md](docs/getting-started.md)

2. **Run**:
    - `pip install -r requirements.txt`
    - `python run.py` then open http://localhost:8000

## Docs

- [docs/README.md](docs/README.md): Doc index
- [docs/getting-started.md](docs/getting-started.md): Setup and run instructions
- [docs/customer-implementation.md](docs/customer-implementation.md): Tutorial to implement the same flow on your side (API client, envelope creation with Smart Anchors, iframe token)
- [CONTRIBUTING.md](CONTRIBUTING.md): How to contribute and what to check before pushing

## Scripts

- `python run.py`: Start the dev server (Flask, port 8000)
