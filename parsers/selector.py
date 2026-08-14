from __future__ import annotations

import re

from parsers.bank_of_america_parser import BankOfAmericaStatementParser
from parsers.base_parser import BaseStatementParser
from parsers.chase_parser import ChaseStatementParser
from parsers.generic_parser import GenericStatementParser


def select_parser(text: str) -> BaseStatementParser:
    preview = text[:3000].upper()
    if "BANK OF AMERICA" in preview or "BANKAMERICARD" in preview:
        return BankOfAmericaStatementParser()
    if re.search(r"\bCHASE\b", preview):
        return ChaseStatementParser()
    return GenericStatementParser()
