from datetime import date

from parsers.generic_parser import normalize_amount, parse_transaction_line


def test_normalize_amount_plain_value():
    assert normalize_amount("$1,234.56") == 1234.56


def test_normalize_amount_parentheses_credit():
    assert normalize_amount("($45.67)") == -45.67


def test_parse_transaction_line():
    transaction = parse_transaction_line("06/12 STARBUCKS 1234 $6.45", default_year=2026, card_name="Test Card")

    assert transaction is not None
    assert transaction.date == date(2026, 6, 12)
    assert transaction.merchant == "STARBUCKS 1234"
    assert transaction.amount == 6.45
    assert transaction.category == "Dining"
    assert transaction.category_rule == "Built-in rule: STARBUCKS"
    assert transaction.card == "Test Card"
