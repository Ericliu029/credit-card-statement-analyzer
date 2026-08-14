from __future__ import annotations

import pandas as pd

from models import Transaction
from parsers import select_parser


DISPLAY_COLUMNS = ["date", "merchant", "amount", "category", "category_rule", "card"]


def parse_statement_text(text: str, card_name: str | None = None) -> tuple[str, list[Transaction]]:
    parser = select_parser(text)
    return parser.issuer_name, parser.parse(text, card_name=card_name)


def transactions_to_dataframe(transactions: list[Transaction]) -> pd.DataFrame:
    if not transactions:
        return pd.DataFrame(columns=DISPLAY_COLUMNS)

    rows = [transaction.to_dict() for transaction in transactions]
    dataframe = pd.DataFrame(rows)
    dataframe["date"] = pd.to_datetime(dataframe["date"]).dt.date
    return dataframe[DISPLAY_COLUMNS]


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"date": "2026-06-01", "merchant": "STARBUCKS 1234", "amount": 6.45, "category": "Dining", "category_rule": "Built-in rule: STARBUCKS", "card": "Chase Freedom Unlimited"},
            {"date": "2026-06-02", "merchant": "WHOLE FOODS MARKET", "amount": 84.12, "category": "Groceries", "category_rule": "Built-in rule: WHOLE FOODS", "card": "Chase Freedom Unlimited"},
            {"date": "2026-06-03", "merchant": "UBER TRIP", "amount": 18.90, "category": "Transportation", "category_rule": "Built-in rule: UBER", "card": "Bank of America Customized Cash Rewards"},
            {"date": "2026-06-04", "merchant": "AMAZON MKTPL", "amount": 129.99, "category": "Shopping", "category_rule": "Built-in rule: AMAZON", "card": "Bank of America Customized Cash Rewards"},
            {"date": "2026-06-05", "merchant": "NETFLIX.COM", "amount": 15.49, "category": "Entertainment", "category_rule": "Built-in rule: NETFLIX", "card": "Chase Freedom Unlimited"},
        ]
    )
