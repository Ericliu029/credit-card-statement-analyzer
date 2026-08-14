# Merchant Categorization

## Purpose

The system maps merchant descriptions from credit card statements to spending categories. Categorization runs entirely on the local computer and does not send statements or merchant information to an external service.

## Where the Rules Come From

The current version does not perform an online lookup at runtime and does not read the bank's Merchant Category Code (MCC). Categories are produced through keyword matching rather than bank-confirmed data:

- Built-in rules are written manually during project development. They may be based on common brand knowledge or an inference from the merchant name and statement context.
- User rules are explicitly saved through the interface and represent a user-confirmed categorization preference.
- `Uncategorized` means that no rule matched; it does not mean transaction parsing failed.

Therefore, matching a rule is not the same as externally verifying a merchant category. The application guarantees that it applies the configured rules consistently, but it does not claim that every built-in rule has been verified online. The reasoning behind manually added rules is recorded in [RULE_DECISIONS.md](RULE_DECISIONS.md).

## Processing Flow

Each transaction is processed in this order:

1. Convert the merchant description to uppercase and collapse extra spaces.
2. Check user-defined rules in `data/custom_merchant_rules.json`.
3. Check built-in project rules in `data/merchant_rules.json`.
4. Return `Uncategorized` if no keyword matches.

The transaction table's `Rule source` column displays the keyword that matched, such as `Built-in rule: WINGSTOP` or `Custom rule: AMAZON MKTPL`. This makes every automatic categorization traceable.

User rules take priority over built-in rules. For example, if the built-in rules map `AMAZON` to `Shopping`, a user may save `AMAZON MKTPL -> Other`. Future transactions containing `AMAZON MKTPL` will then use `Other` first.

## Why Uncategorized Transactions Appear

Credit card statements often provide only a raw merchant description, for example:

```text
TST* PARIS BAGUETTE - ELM ELMHURST NY
```

The description may contain a payment-platform prefix, store number, telephone number, or city. The application does not guess a category from the amount or an ambiguous name. When the rule library has no reliable keyword, it retains `Uncategorized` for user review.

## Handling a New Merchant

### Save a Rule in the Interface

1. Open `Custom Categories` in the sidebar.
2. Enter a stable and distinctive phrase in `Merchant contains`, such as `PARIS BAGUETTE`.
3. Select a category and click `Save rule`.
4. After the page reruns, matching transactions in the current and future statements will use that category.

Do not include dates, amounts, store transaction identifiers, or complete telephone numbers in the keyword. A keyword that is too long may not match another location, while one that is too short may affect unrelated merchants.

A category can also be edited directly in the transaction table, but that edit affects only the current page and exported CSV. Only rules saved through the sidebar are written to the local rules file and reused later.

### Modify the Built-In Rules

Merchants that have been confirmed and are appropriate for most users can be added to `data/merchant_rules.json`. The file maps each category to a list of keywords:

```json
{
  "Dining": ["PARIS BAGUETTE", "WINGSTOP"],
  "Transportation": ["OMNY"]
}
```

Add a test to `tests/test_categorizer.py` after changing the file so that rule ordering cannot introduce a silent misclassification.

## Key Files

- `categorization/categorizer.py`: normalizes merchant names and applies priority-based matching.
- `categorization/rules.py`: loads built-in rules and saves, lists, or removes user rules.
- `data/merchant_rules.json`: project-maintained general rules.
- `data/custom_merchant_rules.json`: local rules saved by the user.
- `tests/test_categorizer.py`: categorization behavior and priority tests.

## Current Limitations

Keyword rules are transparent, fast, and available offline, but they do not understand merchant semantics and cannot automatically disambiguate merchants with similar names. Future versions could add merchant-name cleaning, MCC data, learning from user corrections, or a local machine-learning model. Low-confidence results should still require user confirmation regardless of the method used.

## Verification

Run the following command from the project directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

All tests should pass. A real statement should then be used to verify the transaction count, total spending, and number of uncategorized transactions.
