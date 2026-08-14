from __future__ import annotations

import re
from datetime import date

from categorization import categorize_merchant_with_reason
from models import Transaction
from parsers.card_metadata import detect_card_label
from parsers.generic_parser import GenericStatementParser
from parsers.generic_parser import _detect_statement_date, _detect_statement_year, normalize_amount


BOA_TRANSACTION_PATTERN = re.compile(
    r"^\s*(?P<transaction_month>\d{1,2})/(?P<transaction_day>\d{1,2})\s+"
    r"(?P<posting_month>\d{1,2})/(?P<posting_day>\d{1,2})\s+"
    r"(?P<body>.+?)\s+(?P<amount>-?\$?\d[\d,]*\.\d{2})\s*$"
)
BOA_REFERENCE_PATTERN = re.compile(r"^(?P<merchant>.+?)\s+\d{4}\s+\d{4}$")


class BankOfAmericaStatementParser(GenericStatementParser):
    issuer_name = "Bank of America"

    def parse(self, text: str, card_name: str | None = None) -> list[Transaction]:
        statement_date = _detect_statement_date(text)
        default_year = statement_date.year if statement_date else _detect_statement_year(text)
        card = card_name or detect_card_label(text, self.issuer_name)
        transactions: list[Transaction] = []

        for line in text.splitlines():
            match = BOA_TRANSACTION_PATTERN.match(line)
            if not match:
                continue

            amount = normalize_amount(match.group("amount"))
            if amount == 0:
                continue

            body = " ".join(match.group("body").split())
            reference_match = BOA_REFERENCE_PATTERN.match(body)
            merchant = reference_match.group("merchant") if reference_match else body

            year = default_year
            transaction_month = int(match.group("transaction_month"))
            if statement_date and transaction_month > statement_date.month:
                year -= 1

            category_match = categorize_merchant_with_reason(merchant)
            transactions.append(
                Transaction(
                    date=date(year, transaction_month, int(match.group("transaction_day"))),
                    merchant=merchant,
                    amount=amount,
                    category=category_match.category,
                    category_rule=category_match.explanation,
                    card=card,
                    original_description=line.strip(),
                )
            )

        return transactions
