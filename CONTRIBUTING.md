# Contributing

Thanks for your interest in contributing to this demo app.

## Setup

1. **Clone and install**

    ```bash
    git clone https://github.com/Mikescops/subnoto-demo-python
    cd subnoto-demo-python
    pip install -r requirements.txt
    ```

2. **Environment**

    Copy `.env.example` to `.env` in the project root and set your Subnoto credentials. **Never commit `.env` or `.env.local`** — they are gitignored. See [docs/getting-started.md](docs/getting-started.md).

3. **Run**

    ```bash
    python run.py
    ```

    Open http://localhost:8000.

## Before you push

- Ensure the app runs: `python run.py` and load http://localhost:8000.
- Run `git status` and ensure no `.env` or `.env.local` files are staged. If you have accidentally committed secrets, rotate the affected keys and remove the files from the repository history (e.g. with `git filter-branch` or BFG).

## Pull requests

Open a PR with a clear description of the change.

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities and how we handle secrets.
