from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "merchant_rules.json"
CUSTOM_RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "custom_merchant_rules.json"


@lru_cache(maxsize=1)
def load_category_rules() -> dict[str, list[str]]:
    with RULES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_custom_category_rules() -> dict[str, list[str]]:
    if not CUSTOM_RULES_PATH.exists():
        return {}
    with CUSTOM_RULES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def add_custom_rule(keyword: str, category: str) -> None:
    normalized_keyword = " ".join(keyword.upper().split())
    if not normalized_keyword:
        raise ValueError("Merchant keyword cannot be empty.")

    rules = load_custom_category_rules()
    for existing_category in list(rules):
        rules[existing_category] = [value for value in rules[existing_category] if value != normalized_keyword]
        if not rules[existing_category]:
            del rules[existing_category]

    rules.setdefault(category, []).append(normalized_keyword)
    _write_custom_category_rules(rules)


def remove_custom_rule(keyword: str, category: str) -> None:
    normalized_keyword = " ".join(keyword.upper().split())
    rules = load_custom_category_rules()
    if category not in rules:
        return

    rules[category] = [value for value in rules[category] if value != normalized_keyword]
    if not rules[category]:
        del rules[category]
    _write_custom_category_rules(rules)


def list_custom_rules() -> list[tuple[str, str]]:
    return sorted(
        (keyword, category)
        for category, keywords in load_custom_category_rules().items()
        for keyword in keywords
    )


def _write_custom_category_rules(rules: dict[str, list[str]]) -> None:
    CUSTOM_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CUSTOM_RULES_PATH.open("w", encoding="utf-8") as file:
        json.dump(rules, file, indent=2, ensure_ascii=True)
        file.write("\n")
