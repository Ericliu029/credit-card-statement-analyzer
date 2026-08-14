from __future__ import annotations

import re


CARD_PRODUCTS = (
    ("SAPPHIRE PREFERRED", "Chase Sapphire Preferred"),
    ("SAPPHIRE RESERVE", "Chase Sapphire Reserve"),
    ("FREEDOM UNLIMITED", "Chase Freedom Unlimited"),
    ("FREEDOM FLEX", "Chase Freedom Flex"),
    ("INK BUSINESS PREFERRED", "Chase Ink Business Preferred"),
    ("CUSTOMIZED CASH REWARDS", "Bank of America Customized Cash Rewards"),
    ("UNLIMITED CASH REWARDS", "Bank of America Unlimited Cash Rewards"),
    ("BANKAMERICARD", "BankAmericard"),
)

ACCOUNT_NUMBER_PATTERNS = (
    re.compile(
        r"ACCOUNT\s+(?:NUMBER|NO\.?|#)\s*:?\s*(?:X{4}[\s-]*){2,3}(?P<last4>\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"ACCOUNT\s*(?:NUMBER|NO\.?|#)\s*:?\s*(?:\d{4}[\s-]+){3}(?P<last4>\d{4})",
        re.IGNORECASE,
    ),
)


def detect_card_label(text: str, issuer_name: str) -> str:
    normalized = " ".join(text.upper().split())
    product = next((label for keyword, label in CARD_PRODUCTS if keyword in normalized), None)
    if not product and issuer_name == "Bank of America" and "VISA SIGNATURE" in normalized:
        product = "Bank of America Visa Signature"
    base_label = product or (f"{issuer_name} Card" if issuer_name != "Unknown" else "Unknown Card")

    account_match = next((match for pattern in ACCOUNT_NUMBER_PATTERNS if (match := pattern.search(text))), None)
    if account_match:
        return f"{base_label} (ending {account_match.group('last4')})"
    return base_label
