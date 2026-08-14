# Security and Privacy

## Supported Use

This project is designed for local, single-user use. Streamlit launchers bind to `127.0.0.1` so the financial dashboard is not exposed to the local network.

## Sensitive Data

Never commit or attach:

- Real statement PDFs or screenshots
- CSV exports
- SQLite databases or database sidecar files
- LLM classification caches
- Personal merchant rules
- Complete card numbers, CVV values, credentials, or authentication tokens

The repository `.gitignore` excludes the common forms of these files. Contributors must still inspect staged files before pushing.

## Authentication Scope

The included login is a local access gate. Passwords are derived with PBKDF2-HMAC-SHA256, 600,000 iterations, and a random per-user salt. This implementation is not a complete hosted authentication system and does not provide account recovery, email verification, rate limiting, multi-user authorization, or cross-device sessions.

## Reporting a Security Issue

Do not open a public issue containing financial data or credentials. Contact the repository owner privately and provide only the minimum redacted information needed to reproduce the problem.
