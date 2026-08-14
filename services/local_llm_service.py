from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
PROMPT_VERSION = "merchant-v2"
CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "llm_category_cache.json"

LLM_CATEGORIES = (
    "Dining",
    "Groceries",
    "Transportation",
    "Shopping",
    "Travel",
    "Utilities",
    "Entertainment",
    "Health",
    "Fees",
    "Payments & Credits",
    "Other",
    "Uncategorized",
)

CATEGORY_DEFINITIONS = """
Dining: restaurants, fast food, cafes, bakeries, bars, and prepared-food delivery.
Groceries: supermarkets, grocery stores, food markets, and grocery delivery.
Transportation: public transit, rideshare, taxis, parking, tolls, fuel, and trains.
Shopping: general retail, clothing, electronics, household goods, and online marketplaces.
Travel: airlines, hotels, vacation rentals, car rentals, and travel booking.
Utilities: phone, internet, electricity, gas, water, and recurring household services.
Entertainment: streaming, movies, games, concerts, tickets, and recreation.
Health: pharmacies, doctors, dentists, hospitals, labs, optical, and medical care.
Fees: bank fees, interest charges, late fees, and foreign transaction fees.
Payments & Credits: card payments, statement credits, refunds, and account credits.
Other: an identifiable business type that does not fit another category.
Uncategorized: the merchant type cannot be inferred reliably from the description.
""".strip()

SYSTEM_PROMPT = f"""You classify English-language US credit-card merchant descriptors.
Choose exactly one category using these definitions:

{CATEGORY_DEFINITIONS}

Ignore store numbers, transaction IDs, phone numbers, city names, and state abbreviations.
Use the merchant's business type. For example, WINGSTOP is Dining, OMNY is Transportation,
APPLE.COM/BILL is Shopping, and RENDR PHYSICIANS is Health. Use Uncategorized only when the
business type cannot be inferred. Never invent a business type from an unfamiliar acronym,
opaque payment descriptor, or website domain. For example, BOIST INVE* AD3KFRZ0H BOIST.ORG
must be Uncategorized with low confidence because its business type is not explicit.
Only use confidence above 0.8 when the merchant is a recognized brand or the description
explicitly identifies the business type. Confidence must reflect the evidence in the merchant text.
Return only the requested JSON fields."""

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(LLM_CATEGORIES)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["category", "confidence", "reason"],
    "additionalProperties": False,
}


@dataclass(frozen=True, slots=True)
class LocalLLMResult:
    category: str
    confidence: float
    reason: str
    model: str
    prompt_version: str


class OllamaClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        request_fn: Callable = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._request_fn = request_fn

    def is_ready(self) -> bool:
        try:
            response = self._request_json(Request(f"{self.base_url}/api/tags"), timeout=3)
        except (OSError, URLError, TimeoutError, ValueError):
            return False
        return any(item.get("name") == self.model for item in response.get("models", []))

    def classify(self, merchant: str) -> LocalLLMResult:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": RESULT_SCHEMA,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Merchant: {merchant}"},
            ],
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = self._request_json(request)
        content = json.loads(response["message"]["content"])
        category = content["category"]
        confidence = float(content["confidence"])
        reason = " ".join(str(content["reason"]).split())

        if category not in LLM_CATEGORIES:
            raise ValueError(f"Unsupported LLM category: {category}")
        if not 0 <= confidence <= 1:
            raise ValueError("LLM confidence must be between 0 and 1")
        return LocalLLMResult(category, confidence, reason, self.model, PROMPT_VERSION)

    def _request_json(self, request: Request, timeout: int | None = None) -> dict:
        with self._request_fn(request, timeout=timeout or self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def classify_merchants(
    merchants: list[str],
    client: OllamaClient,
    cache_path: Path = CACHE_PATH,
) -> dict[str, LocalLLMResult]:
    cache = _load_cache(cache_path)
    results: dict[str, LocalLLMResult] = {}
    changed = False

    for merchant in dict.fromkeys(merchants):
        cache_key = _cache_key(merchant, client.model)
        cached = cache.get(cache_key)
        if cached:
            result = LocalLLMResult(**cached)
        else:
            result = client.classify(merchant)
            cache[cache_key] = asdict(result)
            changed = True
        results[merchant] = result

    if changed:
        _write_cache(cache_path, cache)
    return results


def _cache_key(merchant: str, model: str) -> str:
    normalized = " ".join(merchant.upper().split())
    return f"{model}|{PROMPT_VERSION}|{normalized}"


def _load_cache(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_cache(path: Path, cache: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, ensure_ascii=True, sort_keys=True)
        file.write("\n")
    temporary_path.replace(path)
