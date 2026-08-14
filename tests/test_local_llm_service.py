import json
from contextlib import AbstractContextManager

from services.local_llm_service import LocalLLMResult, OllamaClient, classify_merchants


class FakeResponse(AbstractContextManager):
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_ollama_client_requests_and_validates_structured_output():
    captured = {}

    def request_fn(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(
            {
                "message": {
                    "content": json.dumps(
                        {"category": "Dining", "confidence": 0.92, "reason": "Fast food restaurant"}
                    )
                }
            }
        )

    client = OllamaClient(request_fn=request_fn)
    result = client.classify("WINGSTOP 2242 NEW YORK NY")

    assert result == LocalLLMResult(
        "Dining", 0.92, "Fast food restaurant", "llama3.2:3b", "merchant-v2"
    )
    assert captured["payload"]["format"]["properties"]["category"]["type"] == "string"
    assert captured["payload"]["options"]["temperature"] == 0
    assert captured["payload"]["think"] is False


def test_merchant_results_are_cached(tmp_path):
    class FakeClient:
        model = "test-model"

        def __init__(self):
            self.calls = 0

        def classify(self, merchant):
            self.calls += 1
            return LocalLLMResult("Other", 0.75, "Unknown organization", self.model, "merchant-v2")

    client = FakeClient()
    cache_path = tmp_path / "llm_cache.json"

    first = classify_merchants(["BOIST INVE", "BOIST INVE"], client, cache_path)
    second = classify_merchants(["BOIST INVE"], client, cache_path)

    assert first == second
    assert client.calls == 1
    assert json.loads(cache_path.read_text(encoding="utf-8"))
