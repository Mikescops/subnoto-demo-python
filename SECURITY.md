# Security

## Reporting a vulnerability

If you discover a security issue in this project, please report it responsibly:

- **Preferred:** Open a [GitHub Security Advisory](https://github.com/Mikescops/subnoto-demo-python/security/advisories/new) for this repository (if you have access), or contact the maintainers privately.
- **Do not** disclose the issue in a public GitHub issue until it has been addressed.

We will acknowledge your report and work on a fix. Once a fix is released, we can coordinate on public disclosure if appropriate.

## Environment and secrets

- Never commit `.env`, `.env.local`, or any file containing real API keys or secrets.
- Copy `.env.example` to `.env` and fill in your own credentials. See [docs/getting-started.md](docs/getting-started.md).
- If you have accidentally committed secrets, rotate the affected keys immediately and remove the data from the repository history.
