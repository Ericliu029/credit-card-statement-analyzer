# Database Architecture

## Current Phase

The application uses SQLite for durable, single-user history. SQLite is part of
Python, requires no database server, and behaves consistently on Windows and
macOS.

The database is created in the current operating-system user's application-data
directory:

- Windows: `%LOCALAPPDATA%\CreditCardStatementAnalyzer\analyzer.db`
- macOS: `~/Library/Application Support/CreditCardStatementAnalyzer/analyzer.db`
- Linux: `$XDG_DATA_HOME/CreditCardStatementAnalyzer/analyzer.db`

Tests and advanced installations can override the directory with
`CCSA_DATA_DIR`. The database is deliberately kept outside the source and
installation directories so application upgrades do not erase user history.

## Import and Duplicate Detection

1. The application reads the uploaded PDF bytes locally.
2. It calculates a SHA-256 fingerprint of the complete file.
3. The fingerprint is checked against `statements.file_hash`.
4. A new fingerprint is parsed and shown for review.
5. The reviewed transactions are saved only when the user selects
   **Save reviewed transactions to history**.
6. An existing fingerprint is loaded from history instead of being inserted a
   second time.

Renaming a PDF does not bypass duplicate detection because the fingerprint is
based on file content, not the filename.

## Schema Version 2

### `statements`

One row represents one imported PDF statement.

| Column | Purpose |
| --- | --- |
| `id` | Internal primary key |
| `file_hash` | Unique SHA-256 duplicate-detection key |
| `filename` | Original uploaded filename |
| `issuer` | Parser-selected bank |
| `card_label` | Detected card product and optional last four digits |
| `statement_month` | Latest transaction month in the statement |
| `imported_at` | UTC import timestamp |

### `transactions`

Each row belongs to one statement through `statement_id`.

| Column | Purpose |
| --- | --- |
| `transaction_date` | Parsed transaction date |
| `merchant` | Normalized display description |
| `amount_cents` | Integer currency amount, avoiding float rounding errors |
| `category` | Reviewed category |
| `category_rule` | Rule, model, confidence, and reason used for classification |
| `card` | Detected card label |
| `original_description` | Original parsed statement description |

Deleting a statement cascades to its transactions. Indexes cover statement,
date, and category queries. `PRAGMA user_version` records the schema version for
future migrations.

### `users`

The local single-user login stores:

| Column | Purpose |
| --- | --- |
| `username` | Case-insensitive local login name |
| `display_name` | Name shown in the application |
| `password_hash` | PBKDF2-HMAC-SHA256 password result |
| `password_salt` | Random per-user salt |
| `created_at` | UTC account creation timestamp |
| `last_login_at` | UTC timestamp of the latest successful login |

Passwords are never stored in plain text. The password derivation uses 600,000
PBKDF2 iterations and a random 16-byte salt. Login state lives only in the
current Streamlit session, so closing the session requires another login.

This is a local access gate, not production multi-user authentication.
Transactions do not yet have a `user_id`, and the login has no password reset,
email verification, rate limiting, recovery codes, or server-side session
management. Those controls must be implemented before a hosted release.

## What Is Not Stored

- Full card numbers
- CVV values
- Online-banking credentials
- Plain-text passwords
- Original PDF files
- Ollama model files

Only the detected card label and optional last four digits are stored.

## Classification Data

The database stores the result and explanation for each saved transaction, but
the recognition implementation remains version-controlled application code:

- deterministic categorization: `categorization/categorizer.py`
- built-in rules: `data/merchant_rules.json`
- personal rules: `data/custom_merchant_rules.json`
- local LLM prompt and schema: `services/local_llm_service.py`
- parser selection: `parsers/selector.py`

Personal rules remain JSON in the single-user phase. They should move to a
database table with `user_id` before a multi-user release.

## Multi-User Migration

A hosted release should migrate the same logical model to PostgreSQL and add:

- `users`
- `user_id` ownership on cards, statements, transactions, and merchant rules
- managed authentication or securely hashed passwords
- authorization checks on every query
- encrypted backups and retention controls
- database migrations instead of startup-only schema creation

The local SQLite phase validates the data model and product workflow without
prematurely introducing account management or a hosted database.
