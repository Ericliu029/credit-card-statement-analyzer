from categorization import categorize_merchant, categorize_merchant_with_reason
from categorization import add_custom_rule, list_custom_rules, remove_custom_rule
from categorization import rules as category_rules


def test_known_merchant_is_categorized():
    assert categorize_merchant("TST* CHIPOTLE NYC") == "Dining"


def test_category_match_explains_keyword_and_source():
    match = categorize_merchant_with_reason("TST* CHIPOTLE NYC")

    assert match.category == "Dining"
    assert match.keyword == "CHIPOTLE"
    assert match.source == "Built-in"
    assert match.explanation == "Built-in rule: CHIPOTLE"


def test_unknown_merchant_is_uncategorized():
    assert categorize_merchant("SOME NEW MERCHANT") == "Uncategorized"


def test_common_grocery_descriptor_is_categorized():
    assert categorize_merchant("INSTACART *WEGMANS 042") == "Groceries"


def test_restaurant_name_wins_over_apple_keyword():
    assert categorize_merchant("APPLEBEES 01234") == "Dining"


def test_ride_share_food_delivery_is_dining():
    assert categorize_merchant("UBER EATS HELP.UBER.COM") == "Dining"


def test_local_restaurant_descriptors_are_categorized():
    assert categorize_merchant("CASTLE CHICKEN ELMHURST NY") == "Dining"
    assert categorize_merchant("KYO RAMEN Queens NY") == "Dining"
    assert categorize_merchant("SHAXIAN XIAOCHI ELMHURST NY") == "Dining"


def test_omny_is_transportation():
    assert categorize_merchant("OMNY VENDING* NEW YORK NY") == "Transportation"


def test_physician_is_health():
    assert categorize_merchant("RENDR PHYSICIANS 164-66308266 NY") == "Health"


def test_airline_is_travel():
    assert categorize_merchant("QATAR AIR 0004026631415 WASHINGTON DC") == "Travel"


def test_card_payment_is_categorized_separately():
    assert categorize_merchant("AUTOMATIC PAYMENT - THANK YOU") == "Payments & Credits"


def test_merchants_from_additional_statement_are_categorized():
    assert categorize_merchant("CHICK ROCKS 131-27305592 IL") == "Dining"
    assert categorize_merchant("TST* PARIS BAGUETTE - ELM ELMHURST NY") == "Dining"
    assert categorize_merchant("WINGSTOP 2242 212-019-1222 NY") == "Dining"
    assert categorize_merchant("TST*TOFU STORY QUEENS 347-506-0797 NY") == "Dining"


def test_custom_rule_overrides_builtin_rule(tmp_path, monkeypatch):
    custom_path = tmp_path / "custom_merchant_rules.json"
    monkeypatch.setattr(category_rules, "CUSTOM_RULES_PATH", custom_path)

    add_custom_rule("AMAZON MKTPL", "Other")

    assert categorize_merchant("AMAZON MKTPL*AB123") == "Other"
    assert list_custom_rules() == [("AMAZON MKTPL", "Other")]

    remove_custom_rule("AMAZON MKTPL", "Other")
    assert list_custom_rules() == []
    assert categorize_merchant("AMAZON MKTPL*AB123") == "Shopping"
