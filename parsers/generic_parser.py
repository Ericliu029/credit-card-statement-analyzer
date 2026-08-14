from __future__ import annotations

import re
from datetime import date

from categorization import categorize_merchant_with_reason
from models import Transaction
from parsers.base_parser import BaseStatementParser
from parsers.card_metadata import detect_card_label


DATE_PATTERN = r"(?P<month>\d{1,2})[/-](?P<day>\d{1,2})(?:[/-](?P<year>\d{2,4}))?"
AMOUNT_PATTERN = r"(?P<amount>-?\(?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})\)?)"
TRANSACTION_PATTERN = re.compile(
    rf"^\s*{DATE_PATTERN}\s+(?P<merchant>.+?)\s+{AMOUNT_PATTERN}\s*$"
)


def normalize_amount(value: str) -> float:
    cleaned = value.strip().replace("$", "").replace(",", "")
    is_parenthesized = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    amount = float(cleaned)
    return -amount if is_parenthesized else amount


def parse_transaction_line(line: str, default_year: int, card_name: str) -> Transaction | None:
    match = TRANSACTION_PATTERN.match(line)
    if not match:
        return None

    year_text = match.group("year")
    year = default_year
    if year_text:
        year = int(year_text)
        if year < 100:
            year += 2000

    transaction_date = date(year, int(match.group("month")), int(match.group("day")))
    merchant = " ".join(match.group("merchant").split())
    amount = normalize_amount(match.group("amount"))
    category_match = categorize_merchant_with_reason(merchant)

    return Transaction(
        date=transaction_date,
        merchant=merchant,
        amount=amount,
        category=category_match.category,
        category_rule=category_match.explanation,
        card=card_name,
        original_description=line.strip(),
    )


class GenericStatementParser(BaseStatementParser):
    issuer_name = "Generic"

    def parse(self, text: str, card_name: str | None = None) -> list[Transaction]:
        card = card_name or detect_card_label(text, self.issuer_name)
        statement_date = _detect_statement_date(text)
        default_year = statement_date.year if statement_date else _detect_statement_year(text)
        transactions: list[Transaction] = []

        for line in text.splitlines():
            transaction = parse_transaction_line(line, default_year=default_year, card_name=card)
            if transaction:
                line_match = TRANSACTION_PATTERN.match(line)
                if (
                    statement_date
                    and line_match
                    and not line_match.group("year")
                    and transaction.date.month > statement_date.month
                ):
                    transaction.date = transaction.date.replace(year=statement_date.year - 1)
                transactions.append(transaction)

        return transactions


def _detect_statement_year(text: str) -> int:
    years = re.findall(r"\b(20\d{2})\b", text)
    if years:
        return int(years[0])
    return date.today().year


def _detect_statement_date(text: str) -> date | None:
    match = re.search(
        r"STATEMENT(?:\s+CLOSING)?\s+DATE\s*:?\s*(\d{1,2})/(\d{1,2})/(\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    year = int(match.group(3))
    if year < 100:
        year += 2000
    return date(year, int(match.group(1)), int(match.group(2)))
