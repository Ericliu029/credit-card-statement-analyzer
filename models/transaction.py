from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(slots=True)
class Transaction:
    date: date
    merchant: str
    amount: float
    category: str = "Uncategorized"
    category_rule: str = "No matching rule"
    card: str = "Unknown"
    original_description: str = ""

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data
