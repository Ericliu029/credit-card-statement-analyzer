# Local LLM Categorization Design

## Decision

A local LLM is suitable as a fallback classifier for unknown merchants. It should not replace PDF parsing, user-defined rules, or confirmed deterministic rules. The recommended hybrid flow is:

1. User-defined rules: highest priority because they represent confirmed user preferences.
2. Built-in keyword rules: handle stable and maintained common merchants.
3. Local LLM: processes only merchants that the first two layers cannot identify.
4. Manual confirmation: retains `Uncategorized` when the LLM has low confidence or the category remains ambiguous.

The current implementation uses Ollama's local HTTP API and `llama3.2:3b`. Merchant descriptions are in English, so the selected model is a text-only model of approximately 2 GB and does not depend on Chinese-language or vision capabilities. The same API, model tag, prompt, and JSON Schema work on Windows and macOS.

Official references:

- Ollama Windows documentation: https://docs.ollama.com/windows
- Ollama macOS documentation: https://docs.ollama.com/macos
- Structured Outputs: https://docs.ollama.com/capabilities/structured-outputs
- llama3.2 model page: https://ollama.com/library/llama3.2

## Why the LLM Does Not Parse the Entire Statement

Transaction extraction requires exact amounts, dates, and column positions. An LLM may omit transactions, alter amounts, or generate nonexistent records. Bank-specific parsers should first produce deterministic transaction data. Only the merchant description should then be passed to the local LLM for categorization.

## Recommended Input

Send only the minimum information required for classification:

```json
{
  "merchant": "TST*TOFU STORY QUEENS 347-506-0797 NY",
  "allowed_categories": ["Dining", "Groceries", "Transportation", "Shopping", "Travel", "Utilities", "Entertainment", "Health", "Fees", "Other"]
}
```

Do not send a name, address, account number, complete statement text, or other transactions to the model.

## Required Output

The model must return structured JSON:

```json
{
  "category": "Dining",
  "confidence": 0.82,
  "reason": "Merchant name suggests a restaurant"
}
```

A result can be applied automatically only when its category is in the allowed list and its confidence reaches the configured threshold. The interface must identify the source as `Local LLM`; it must not present the result as a bank MCC or a verified rule.

The confidence is self-reported by the model and is not a statistically calibrated probability of correctness. By default, the interface displays suggestions without changing categories automatically. The threshold controls automatic application only after the user enables `Auto-apply high-confidence results`.

## Privacy and Operation

- The model must run locally, with no network classification call enabled by default.
- The LLM must remain optional so that the rule system works independently.
- Model name, version, prompt version, and confidence should be included in exported results.
- The first model download requires explicit user consent because the model file is large.
- Cache keys include the model name and prompt version so a prompt upgrade cannot reuse obsolete decisions.

## Evaluation

Before enabling automatic categorization, create a user-confirmed merchant test set. Measure rule coverage, LLM accuracy, low-confidence rate, and manual correction rate separately. A reduction in `Uncategorized` transactions is not sufficient evidence of success because a wrong category can be more harmful than retaining an unknown result.
