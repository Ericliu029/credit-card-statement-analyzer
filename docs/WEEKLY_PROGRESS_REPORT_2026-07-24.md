# Credit Card Statement Analyzer Weekly Progress Report

**Report date: July 24, 2026**
**Project design: Eric Liu**

## 1. Weekly Objective

This week's objective was to advance the project from a demonstration that temporarily generated charts after a PDF upload into a practical personal finance application that can run locally, explain its recognition process, preserve historical records, and provide basic access control.

The work focused on six areas: statement parsing, merchant categorization, credit card identification, historical data storage, local login, and local operation and packaging for Windows and macOS.

## 2. Complete Processing Flow

After a user uploads one or more credit card statement PDFs, the application performs the following steps:

1. Extract PDF text locally with `pdfplumber`. The original PDF is not uploaded to the cloud.
2. Select the Bank of America, Chase, or generic parser based on bank identifiers in the text.
3. Parse transaction dates, merchant descriptions, and amounts, and detect the credit card product and last four digits.
4. Categorize merchants with user-defined rules first and built-in keyword rules second.
5. Optionally call a local Ollama model for merchants that remain unidentified by the rules.
6. Let the user review each category and its recorded reason in the interface.
7. Save the confirmed statement and transactions to a local SQLite database.
8. Read stored data on the History page and generate summaries by month, card, and category.

## 3. Statement and Credit Card Identification

Bank selection is implemented in `parsers/selector.py`. The application checks the beginning of the statement for identifiers such as `BANK OF AMERICA`, `BANKAMERICARD`, or `CHASE`, selects the corresponding parser, and falls back to the generic parser when the issuer cannot be confirmed.

This week's work fixed an issue that incorrectly parsed Bank of America statements and improved card detection for Chase and Bank of America. The product name is inferred from statement keywords such as `FREEDOM UNLIMITED`, `SAPPHIRE PREFERRED`, or `CUSTOMIZED CASH REWARDS`. The application extracts only the last four account digits and does not retain a complete card number or CVV.

The relevant implementation is located in:

- `parsers/bank_of_america_parser.py`
- `parsers/generic_parser.py`
- `parsers/card_metadata.py`
- `services/transaction_service.py`

## 4. Merchant Categorization Logic

Categorization is not an online merchant lookup and is not an unexplained guess. The current implementation uses an explainable hybrid pipeline:

1. **User rules first:** read `data/custom_merchant_rules.json`.
2. **Built-in rules second:** read `data/merchant_rules.json`.
3. **Local LLM fallback:** process only merchants that remain `Uncategorized`.
4. **Manual review:** retain `Uncategorized` when evidence or model confidence is insufficient.

The deterministic classifier normalizes letter case and whitespace before applying keyword containment matching. Each transaction also records its categorization source, such as `Built-in rule: STARBUCKS`, `Custom rule`, or the local model name, prompt version, confidence, and explanation.

Deterministic rule application is implemented in `categorization/categorizer.py`, and rule loading and persistence are implemented in `categorization/rules.py`. This structure allows a mentor or reviewer to inspect the priority order and exact keywords instead of treating categorization as a black box.

## 5. Local LLM Categorization

The application uses Ollama with `llama3.2:3b`. Windows and macOS use the same API and prompt. The model runs locally through `http://localhost:11434`, so merchant descriptions are not sent to a cloud service for classification.

The model must choose from a fixed category list and return structured JSON containing `category`, `confidence`, and `reason`. Temperature is set to 0 to reduce inconsistent results for the same merchant. A high-confidence result can be applied automatically when the user enables that option; a low-confidence result remains a suggestion.

The prompt, category definitions, JSON Schema, and prompt version are defined in `services/local_llm_service.py`. Results are cached in `data/llm_category_cache.json`. The cache key includes the model, prompt version, and normalized merchant name.

The project deliberately distinguishes between reducing `Uncategorized` results and improving accuracy. A wrong category may be more harmful than an unknown one, so the system does not force a guess for every merchant.

## 6. SQLite History Database

Previously, the project had no database: transactions existed only in the current Streamlit session and disappeared after the application closed. This week introduced SQLite schema version 2. The database is stored in the user's operating-system data directory rather than the application installation directory:

- Windows: `%LOCALAPPDATA%\CreditCardStatementAnalyzer\analyzer.db`
- macOS: `~/Library/Application Support/CreditCardStatementAnalyzer/analyzer.db`

The `statements` table stores the file fingerprint, file name, bank, card label, statement month, and import timestamp. The `transactions` table stores the date, merchant, amount, category, categorization reason, card, and original description. Amounts are stored as integer cents to avoid floating-point precision errors.

The application calculates a SHA-256 fingerprint from the complete PDF contents and uses it as the statement's unique key. Renaming a file does not bypass duplicate detection: if its contents are unchanged, the application identifies it as already imported and reads the existing records instead of inserting a duplicate.

The database implementation is in `services/database_service.py`, with the full design documented in `docs/DATABASE.md`. The database does not store original PDFs, complete card numbers, CVVs, or online banking credentials.

## 7. Login Interface

On the first launch, the user creates a local account. A login is required on later launches before statements or the History page can be accessed. The interface now includes a custom application icon, login state, sign-out control, and `Designed by Eric Liu` attribution.

Passwords are not stored as plain text. The database stores a random 16-byte salt and a PBKDF2-HMAC-SHA256 result produced with 600,000 iterations. Authentication state is stored in the current Streamlit session.

This login is currently a local single-user access gate, not production multi-user authentication. Transactions are not yet isolated by `user_id`, and the application does not provide password reset, email verification, login rate limiting, recovery codes, or server-side session management. These limitations are recorded explicitly in the database documentation.

## 8. Historical Analysis and Interface Improvements

The application now provides two work areas: `Analyze` and `History`. Analyze handles upload, categorization, review, and saving. History provides long-term analysis of stored records.

Historical data can be filtered by month and credit card. The dashboard shows total spending, transaction count, average amount, categorization completion, monthly change, daily spending, category share, largest expenses, and spending by card. The pie chart displays category names and percentages directly, while the category amount units below use matching icons.

Multiple statements can be combined in a single analysis, and the month filter can compare different statement cycles. Card charts display the parsed bank product and last four digits instead of using PDF file names as card names.

## 9. Cross-Platform Operation and Security

Windows uses a local batch launcher. macOS uses a transferable ZIP package with installation and startup scripts. The macOS installer creates an isolated Python environment and, when necessary, guides the user through installing Ollama and downloading the model.

Both platform launchers bind Streamlit to `127.0.0.1` so the financial dashboard is not exposed to other devices on the local network. This address is accessible only from the computer running the application. It is not a public URL that can be shared with a mentor or another device, and it becomes unavailable when the local process stops.

## 10. Testing and Verification

At the time of this report, **33 automated tests pass**. They cover:

- Bank of America and generic statement parsing
- Credit card product and last-four identification
- Built-in rules, custom rules, and rule priority
- Local LLM structured output, caching, and error handling
- SQLite persistence, amount precision, queries, deletion, and duplicate detection
- Schema migration from version 1 to version 2 without losing history
- Password verification and confirmation that plain-text passwords are absent from the database
- First-run account creation, sign-out, and subsequent login

The Streamlit Analyze, History, and login screens also received application-level runtime testing.

## 11. Current Limitations

- Parsing is reliable only for the bank formats currently implemented. A new bank or redesigned statement still requires a parser update and a regression sample.
- The local LLM cannot guarantee correct categorization for every unfamiliar merchant; confidence controls and manual review remain necessary.
- SQLite is appropriate for a local single-user application but not for concurrent writes from multiple devices or an internet-based multi-user service.
- The current login does not isolate data among multiple users and must not be used directly as public website authentication.
- The local URL depends on a continuously running Streamlit process and cannot be shared directly with a mentor or another device.
- The macOS ZIP is not yet an Apple Developer-signed and notarized DMG.

## 12. Recommended Next Phase

The next phase should first add `user_id` ownership to `statements`, `transactions`, `cards`, and `merchant_rules` to establish a real data boundary. The SQLite data model can then be migrated to PostgreSQL and connected to a mature authentication provider.

A production release would also require HTTPS, server-side sessions, login rate limiting, password recovery, formal database migrations, encrypted backups, a privacy policy, and user-controlled data deletion. Parser development should continue with redacted multi-bank samples and measurable evaluation metrics such as parsing accuracy, rule coverage, low-confidence rate, and manual correction rate.

## 13. Topics to Discuss With the Mentor

1. Should the first release remain a local desktop tool or become a hosted multi-user service?
2. Should the application preserve original PDFs or only structured transactions?
3. How should the project balance wrong categorizations against retained `Uncategorized` results?
4. Which bank and card formats are required for the first supported release?
5. Should authentication use school or company SSO, third-party OAuth, or application-managed accounts?
6. Does the product need cross-device synchronization, data import and export, and user-controlled deletion of all stored data?
7. Should project evaluation emphasize parsing accuracy, categorization accuracy, or the completeness of the overall product workflow?
