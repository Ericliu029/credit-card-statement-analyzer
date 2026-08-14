import sqlite3

from services.database_service import Database, default_database_path, statement_fingerprint


TRANSACTIONS = [
    {
        "date": "2026-07-01",
        "merchant": "TEST CAFE",
        "amount": 10.125,
        "category": "Dining",
        "category_rule": "Built-in rule: CAFE",
        "card": "Test Card (ending 1234)",
        "original_description": "TEST CAFE NY",
    },
    {
        "date": "2026-07-02",
        "merchant": "PAYMENT",
        "amount": -5,
        "category": "Payments & Credits",
        "category_rule": "Built-in rule: PAYMENT",
        "card": "Test Card (ending 1234)",
        "original_description": "PAYMENT",
    },
]


def test_statement_fingerprint_is_stable_and_content_based():
    assert statement_fingerprint(b"statement") == statement_fingerprint(b"statement")
    assert statement_fingerprint(b"statement") != statement_fingerprint(b"other")


def test_database_directory_can_be_overridden(tmp_path, monkeypatch):
    monkeypatch.setenv("CCSA_DATA_DIR", str(tmp_path))

    assert default_database_path() == tmp_path / "analyzer.db"


def test_local_user_can_be_created_and_authenticated(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()

    user = database.create_user("Eric", "secure-pass-2026", "Eric Liu")

    assert database.has_users() is True
    assert user["username"] == "eric"
    assert user["display_name"] == "Eric Liu"
    assert database.authenticate_user("ERIC", "secure-pass-2026") == user
    assert database.authenticate_user("eric", "wrong-password") is None


def test_local_user_password_is_not_stored_in_plain_text(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()
    password = "secure-pass-2026"

    database.create_user("eric", password)

    database_bytes = database.path.read_bytes()
    assert password.encode("utf-8") not in database_bytes


def test_local_user_requires_a_reasonable_password(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()

    try:
        database.create_user("eric", "short")
    except ValueError as error:
        assert "at least 8" in str(error)
    else:
        raise AssertionError("Expected a short password to be rejected.")


def test_schema_one_database_is_upgraded_without_losing_history(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()
    database.save_statement(
        file_hash="existing-history",
        filename="existing.pdf",
        issuer="Test Bank",
        transactions=TRANSACTIONS,
    )
    with sqlite3.connect(database.path) as connection:
        connection.execute("DROP TABLE users")
        connection.execute("PRAGMA user_version = 1")

    database.initialize()

    assert len(database.list_statements()) == 1
    assert len(database.load_transactions()) == 2
    assert database.has_users() is False


def test_database_saves_statement_and_transactions(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()

    inserted = database.save_statement(
        file_hash="abc123",
        filename="july.pdf",
        issuer="Test Bank",
        transactions=TRANSACTIONS,
    )

    assert inserted is True
    assert database.statement_exists("abc123") is True
    rows = database.load_transactions()
    assert len(rows) == 2
    assert rows[1]["merchant"] == "TEST CAFE"
    assert rows[1]["amount"] == 10.13
    assert rows[1]["statement_filename"] == "july.pdf"

    statements = database.list_statements()
    assert statements[0]["card_label"] == "Test Card (ending 1234)"
    assert statements[0]["transactions"] == 2
    assert statements[0]["spending"] == 10.13


def test_duplicate_statement_is_not_inserted_twice(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()

    first = database.save_statement(
        file_hash="same-file",
        filename="july.pdf",
        issuer="Test Bank",
        transactions=TRANSACTIONS,
    )
    second = database.save_statement(
        file_hash="same-file",
        filename="renamed.pdf",
        issuer="Test Bank",
        transactions=TRANSACTIONS,
    )

    assert first is True
    assert second is False
    assert len(database.list_statements()) == 1
    assert len(database.load_transactions()) == 2


def test_deleting_statement_cascades_to_transactions(tmp_path):
    database = Database(tmp_path / "analyzer.db")
    database.initialize()
    database.save_statement(
        file_hash="delete-me",
        filename="old.pdf",
        issuer="Test Bank",
        transactions=TRANSACTIONS,
    )
    statement_id = database.list_statements()[0]["id"]

    assert database.delete_statement(statement_id) is True
    assert database.list_statements() == []
    assert database.load_transactions() == []
