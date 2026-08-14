from __future__ import annotations

from dataclasses import dataclass

from .rules import load_category_rules, load_custom_category_rules


@dataclass(frozen=True, slots=True)
class CategoryMatch:
    category: str
    keyword: str | None
    source: str

    @property
    def explanation(self) -> str:
        if not self.keyword:
            return "No matching rule"
        return f"{self.source} rule: {self.keyword}"


def normalize_merchant(value: str) -> str:
    return " ".join(value.upper().split())


def categorize_merchant(merchant: str) -> str:
    return categorize_merchant_with_reason(merchant).category


def categorize_merchant_with_reason(merchant: str) -> CategoryMatch:
    normalized = normalize_merchant(merchant)
    for source, rules in (("Custom", load_custom_category_rules()), ("Built-in", load_category_rules())):
        match = _match_category(normalized, rules, source)
        if match:
            return match
    return CategoryMatch("Uncategorized", None, "None")


def _match_category(
    normalized_merchant: str, rules: dict[str, list[str]], source: str
) -> CategoryMatch | None:
    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword.upper() in normalized_merchant:
                return CategoryMatch(category, keyword, source)
    return None
