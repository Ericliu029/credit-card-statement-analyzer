from __future__ import annotations

from abc import ABC, abstractmethod

from models import Transaction


class BaseStatementParser(ABC):
    issuer_name = "Unknown"

    @abstractmethod
    def parse(self, text: str, card_name: str | None = None) -> list[Transaction]:
        raise NotImplementedError
