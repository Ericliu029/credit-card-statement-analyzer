from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping


APP_DIRECTORY_NAME = "CreditCardStatementAnalyzer"
SCHEMA_VERSION = 2
PASSWORD_ITERATIONS = 600_000


def default_database_path() -> Path:
    override = os.getenv("CCSA_DATA_DIR")
    if override:
        data_directory = Path(override).expanduser()
    elif sys.platform == "darwin":
        data_directory = Path.home() / "Library" / "Application Support" / APP_DIRECTORY_NAME
    elif os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        data_directory = (
            Path(local_app_data) / APP_DIRECTORY_NAME
            if local_app_data
            else Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME
        )
    else:
        data_directory = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        data_directory = data_directory / APP_DIRECTORY_NAME
    return data_directory / "analyzer.db"


DEFAULT_DATABASE_PATH = default_database_path()


def statement_fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class Database:
    def __init__(self, path: Path | str = DEFAULT_DATABASE_PATH) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema {current_version} is newer than supported version {SCHEMA_VERSION}."
                )
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS statements (
                    id INTEGER PRIMARY KEY,
                    file_hash TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    card_label TEXT NOT NULL,
                    statement_month TEXT,
                    imported_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    statement_id INTEGER NOT NULL
                        REFERENCES statements(id) ON DELETE CASCADE,
                    transaction_date TEXT NOT NULL,
                    merchant TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    category_rule TEXT NOT NULL,
                    card TEXT NOT NULL,
                    original_description TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_transactions_statement
                    ON transactions(statement_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_date
                    ON transactions(transaction_date);
                CREATE INDEX IF NOT EXISTS idx_transactions_category
                    ON transactions(category);
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def has_users(self) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return row is not None

    def create_user(self, username: str, password: str, display_name: str = "") -> dict[str, object]:
        normalized_username = _normalize_username(username)
        normalized_display_name = " ".join(display_name.split()) or normalized_username
        _validate_password(password)
        salt = os.urandom(16)
        password_hash = _hash_password(password, salt)
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        username, display_name, password_hash,
                        password_salt, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_username,
                        normalized_display_name,
                        password_hash.hex(),
                        salt.hex(),
                        created_at,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("That username already exists.") from error
        return {
            "id": int(cursor.lastrowid),
            "username": normalized_username,
            "display_name": normalized_display_name,
        }

    def authenticate_user(self, username: str, password: str) -> dict[str, object] | None:
        normalized_username = " ".join(username.strip().split()).lower()
        if not normalized_username or not password:
            return None

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, password_hash, password_salt
                FROM users
                WHERE username = ?
                """,
                (normalized_username,),
            ).fetchone()
            if row is None:
                return None

            candidate = _hash_password(password, bytes.fromhex(row["password_salt"]))
            if not hmac.compare_digest(candidate, bytes.fromhex(row["password_hash"])):
                return None

            connection.execute(
                "UPDATE users SET last_login_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), row["id"]),
            )
        return {
            "id": int(row["id"]),
            "username": str(row["username"]),
            "display_name": str(row["display_name"]),
        }

    def statement_exists(self, file_hash: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM statements WHERE file_hash = ?",
                (file_hash,),
            ).fetchone()
        return row is not None

    def save_statement(
        self,
        *,
        file_hash: str,
        filename: str,
        issuer: str,
        transactions: Iterable[Mapping[str, object]],
    ) -> bool:
        rows = list(transactions)
        if not rows:
            raise ValueError("A statement must contain at least one transaction.")

        card_label = _most_common_value(rows, "card", "Unknown Card")
        dates = sorted(str(row["date"])[:10] for row in rows)
        statement_month = dates[-1][:7] if dates else None
        imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO statements (
                        file_hash, filename, issuer, card_label,
                        statement_month, imported_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_hash,
                        filename,
                        issuer,
                        card_label,
                        statement_month,
                        imported_at,
                    ),
                )
            except sqlite3.IntegrityError:
                return False

            statement_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO transactions (
                    statement_id, transaction_date, merchant, amount_cents,
                    category, category_rule, card, original_description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        statement_id,
                        str(row["date"])[:10],
                        str(row.get("merchant", "")),
                        _amount_to_cents(row.get("amount", 0)),
                        str(row.get("category") or "Uncategorized"),
                        str(row.get("category_rule") or "No matching rule"),
                        str(row.get("card") or card_label),
                        str(row.get("original_description") or ""),
                    )
                    for row in rows
                ],
            )
        return True

    def load_transactions(self, file_hash: str | None = None) -> list[dict[str, object]]:
        where_clause = "WHERE s.file_hash = ?" if file_hash else ""
        parameters = (file_hash,) if file_hash else ()
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    t.id,
                    t.transaction_date AS date,
                    t.merchant,
                    t.amount_cents,
                    t.category,
                    t.category_rule,
                    t.card,
                    t.original_description,
                    s.id AS statement_id,
                    s.file_hash AS statement_hash,
                    s.filename AS statement_filename,
                    s.issuer,
                    s.imported_at
                FROM transactions AS t
                JOIN statements AS s ON s.id = t.statement_id
                {where_clause}
                ORDER BY t.transaction_date DESC, t.id DESC
                """,
                parameters,
            ).fetchall()
        return [
            {
                **dict(row),
                "amount": row["amount_cents"] / 100,
            }
            for row in rows
        ]

    def list_statements(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.id,
                    s.filename,
                    s.issuer,
                    s.card_label,
                    s.statement_month,
                    s.imported_at,
                    COUNT(t.id) AS transactions,
                    COALESCE(SUM(CASE WHEN t.amount_cents > 0 THEN t.amount_cents ELSE 0 END), 0)
                        AS spending_cents
                FROM statements AS s
                LEFT JOIN transactions AS t ON t.statement_id = s.id
                GROUP BY s.id
                ORDER BY s.imported_at DESC
                """
            ).fetchall()
        return [
            {
                **dict(row),
                "spending": row["spending_cents"] / 100,
            }
            for row in rows
        ]

    def delete_statement(self, statement_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM statements WHERE id = ?",
                (statement_id,),
            )
        return cursor.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection


def _amount_to_cents(value: object) -> int:
    decimal_value = Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(decimal_value * 100)


def _normalize_username(value: str) -> str:
    username = " ".join(value.strip().split()).lower()
    if len(username) < 3:
        raise ValueError("Username must contain at least 3 characters.")
    if len(username) > 64:
        raise ValueError("Username cannot exceed 64 characters.")
    return username


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if len(password) > 256:
        raise ValueError("Password cannot exceed 256 characters.")


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )


def _most_common_value(
    rows: list[Mapping[str, object]],
    key: str,
    default: str,
) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or default)
        counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get, default=default)
